

from langchain.memory import ConversationSummaryMemory
from langchain.memory.buffer import ConversationBufferMemory

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
import logging
import tiktoken 
from langchain.memory.chat_message_histories.in_memory import \
    ChatMessageHistory


logger = logging.getLogger(__name__)

def make_llm(variant):
    
    llm = ChatOpenAI(model_name=variant)
    
    return llm



def num_tokens_from_string(string: str, model: str = 'gpt-4') -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def add_history_to_summary_memory(chat_history, llm):
    """ For making a summarised memory from a chat history."""
    memory = ConversationSummaryMemory(llm=llm, return_messages=True)

    # We initialize placeholders for the current input and output
    current_input = None
    current_output = ""

    for message in chat_history:
        if isinstance(message, HumanMessage):
            # If we have an existing input and output (from previous loop iterations)
            # we save them and then reset both
            if current_input:
                memory.save_context({"input": current_input}, {
                                    "output": current_output})
                current_input = None
                current_output = ""

            # Update current_input with the current HumanMessage content
            current_input = message.content

        elif isinstance(message, AIMessage):
            # If we have an existing output (from previous AI messages), concatenate it
            # with the new AIMessage content, separated by a space for readability.
            if current_output:
                current_output += " " + message.content
            else:
                current_output = message.content

    # After iterating, if there's an input left (with or without an output),
    # we save it. This handles the case of a trailing Human message or a Human-AI sequence at the end.
    if current_input:
        memory.save_context({"input": current_input}, {
                            "output": current_output})

    return memory


def summarise_history(message_history, llm):
    summary_memory = add_history_to_summary_memory(message_history, llm)
    summarised_history = summary_memory.load_memory_variables({})
    return summarised_history["history"]


def summarise_chat_history(writing_chain, llm_summariser, n_tokens_when_summarise, summarisation_window=1000):
    # Summarise the chat history if it has become long
    message_history = writing_chain.memory.chat_memory.messages
    message_history_string = str(message_history).replace("additional_kwargs={}, example=False", "")
    logger.info('Message history: \n')
    for message in message_history:
        logger.info(message)

    # Update the memory of the main writing chain with the summarised history
    history_length = num_tokens_from_string(message_history_string)
    if history_length > n_tokens_when_summarise:
        # only summarise it once, not after every message
        logger.info(f"Number of tokens: {history_length}")
        summary_memory = add_history_to_summary_memory(message_history, llm_summariser)
        summarised_history = summary_memory.load_memory_variables({})

        # Retrieve the SystemMessages from the message_history, because we want to include them in the summarised memory
        # The tour results for example are SystemMessages.
        message_history_system_messages = [
            message for message in message_history if isinstance(message, SystemMessage)]

        # Combine the summary with the system messages:
        if n_tokens_when_summarise == int(summarisation_window):
            # we add the system messages after the first summarisation
            compressed_chat_history = summarised_history["history"] + message_history_system_messages
        else:
            # but if we summarise again, we want the most recent summary to be in the end
            compressed_chat_history = message_history_system_messages + summarised_history["history"]

        # this is a string, should have the summary + the system messages:
        history_summary = ' '.join([message.content for message in compressed_chat_history])
        logger.info(f'History summary + system messages:\n\n {history_summary}')
        logger.info(f"History summary length: {num_tokens_from_string(history_summary)}")

        # Update the memory of the main writing chain with the summarised history
        updated_history = ChatMessageHistory(messages=compressed_chat_history)
        writing_chain.memory = ConversationBufferMemory(chat_memory=updated_history, return_messages=True)

        logger.info("summarised memory:")
        logger.info(writing_chain.memory.chat_memory.messages)

        # let's summarise again when the history becomes long again
        n_tokens_when_summarise += n_tokens_when_summarise

    return n_tokens_when_summarise
