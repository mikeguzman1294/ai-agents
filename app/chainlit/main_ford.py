import json
import sys
from pathlib import Path

import chainlit as cl
import chainlit.input_widget as cl_input_widget
from chainlit.input_widget import Select, Slider
from loguru import logger

# Ensure all repository's custom modules can be imported
PARENT_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.append(PARENT_DIR)

from app_config import AppConfig, ChatConfig
from in_vehicle_assistant.agents import MultiAgentSystem
from in_vehicle_assistant.gcp.bq_log_chatbot import BQFeedback, BQLogger
from in_vehicle_assistant.llm.llm_client import MODEL_INFO

# Get application and chat settings
app_config = AppConfig()
chat_config = ChatConfig()

# Determine the application scope string label
app_scope = "dev" if app_config.DEVELOPER_MODE else "prod"

# Set-up Q&A interaction logger mechanism
logger_table = f"{app_scope}_feedback"
bq_logger = BQLogger(
    project_id=app_config.PROJECT_ID,
    logger_db=chat_config.FEEDBACK_LOGGER_BQ_DS,
    logger_table=logger_table,
)

# Set-up user feedback mechanism
feedback_table = f"{app_scope}_feedback"
cl_data_layer = BQFeedback(
    project_id=app_config.PROJECT_ID,
    logger_db=chat_config.FEEDBACK_LOGGER_BQ_DS,
    logger_table=feedback_table,
)


@cl.on_chat_start
async def on_chat_start() -> None:
    """This function is called when a new chat session is created.

    It serves as an initialization routine.

    Args:
        None

    Returns:
        None
    """
    # Log session beginning to terminal for debug
    logger.info("A new chat session has started.")

    # Get and set the chat session user's username
    # For more information on Chainlit user session refer to:
    # https://docs.chainlit.io/concepts/user-session
    app_user = cl.user_session.get("user")
    if app_user:
        cl.user_session.set("username", app_user.identifier)
    else:
        cl.user_session.set("username", "anonymous")

    # Enable settings button and initialize widget values
    settings_widgets = [
        Select(
            id="model",
            label="Small Language Model (SLM)",
            values=MODEL_INFO.keys(),
            initial_value=chat_config.DEFAULT_LLM_MODEL,
            description="SLM to generate answers",
        ),
    ]

    # If developer mode is set, allow the user to configure MAS advanced settings
    if app_config.DEVELOPER_MODE:
        settings_widgets.extend([
            Slider(
                id="temperature",
                label="Temperature",
                initial_value=chat_config.TEMPERATURE,
                min=0,
                max=1,
                step=0.05,
                description="Lower the temperature, lower the randomness in answer.",
            ),
        ])

    settings = await cl.ChatSettings(settings_widgets).send()

    # Initialize the Multi-Agent System
    mas_client = MultiAgentSystem(
        model=settings.get("model"),
        temperature=settings.get("temperature"),
        chat_config=chat_config.TEMPERATURE,  # This seems like a typo, should probably be just chat_config
    )
    cl.user_session.set("mas_client", mas_client)

    # Set user session MAS client
    cl.user_session.set("mas_client", mas_client)


@cl.on_settings_update
async def setup_graph(settings: dict) -> None:
    """
    This function is called whenever there is a change in the chat settings widget.
    """
    # Retrieve the MAS client
    mas_client = cl.user_session.get("mas_client")
    mas_client.initialize_graph(
        model=settings.get("model"), temperature=settings.get("temperature"), chat_config=chat_config.TEMPERATURE # Also seems like a typo here.
    )
    cl.user_session.set("mas_client", mas_client)

    # Display the updated settings with a JSON-type layout
    output = f"Settings updated!\n```json\n{json.dumps(settings, indent=2)}\n```"
    # TODO: Check updated version for disabling messages feedback
    await cl.Message(content=output).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """
    It sends back an intermediate response from the tool, followed by the final answer.
    """
    # log user prompt information for tracing
    logger.info(f"User prompt! {message.to_dict()}")

    # Retrieve the RAG client and invoke the chain
    mas_client = cl.user_session.get("mas_client")
    all_messages_str = mas_client.process_message(message=message.content)

    # An element is a piece of content that can be attached to a Message or Step and displayed on the user interface.
    # For Elements, refer to: https://docs.chainlit.io/concepts/elements
    # The Text class allows you to display a text element in the chatbot UI.
    # Text class takes a string and creates a text element that can be sent to the UI.
    # For more elements, refer to: https://docs.chainlit.io/concepts/elements
    elements = [
        cl.Text(
            content=all_messages_str, display="inline", language="html"
        )
    ]
    # Send the graph response to the UI and retrieve the reply message identifier
    # This ID will identify the whole query, reply tuple in the QA logging analysis
    await cl.Message(content=all_messages_str, elements=elements).send()

    # Log the interaction into BigQuery
    chat_log = {
        "query_id": message.parent_id,
        "user_id": cl.user_session.get("username"),
        "question": message.content,
        "response": all_messages_str,
        "stepwise_response": all_messages_str,
        "model": cl.user_session.get("chat_settings")["model"],
    }
    status = bq_logger.insert_chat_log(chat_log)
    logger.info(f"logger status: {status}")


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
) -> cl.User | None:
    """
    Handles the OAuth callback process after authentication with an external provider.

    For general documentation on Chainlit authentication services, refer to:
    https://docs.chainlit.io/authentication/overview

    For specific documentation on Microsoft Entra (previously Azure AD) authentication for Chainlit, refer to:
    https://docs.chainlit.io/authentication/oauth#azure-active-directory

    Args:
        provider_id (str): The unique identifier for the OAuth provider.
        token (str): The authentication token received from the OAuth provider.
        raw_user_data (dict[str, str]): A dictionary containing raw user data returned by the provider.
        default_user (cl.User): The default user object to be returned if no specific user
            is found or created during the callback processing.

    Returns:
        cl.User | None: The user object associated with the authenticated session, or None if the
            authentication process fails or the user is not found.
    """
    return default_user