
def verify_doc(recipient, messages, sender, config):
    return f'''Verify the following content. 
            \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}'''

def verify_system_doc_message(recipient, messages, sender, config):
    return f'''Verify the following content by comparing the documents in the directory path at './templates/'. 
            \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}'''

def verify_wtemplate_sysmessage(verifier_name):
    return f'''Your role is an {verifier_name} Verifier. Your task is to compare the user's {verifier_name}
against the template provided to you. Provide a precise response, verifying if it has a similar structure as the template. PLEASE NOTE that it does not have to be exactly the same, and having minor differences is okay. 
DO NOT use any code to verify the content.'''

# '''
#             Your role is an {verifier_name} Verifier. Your task is to check the contents of a dictionary/dictionaries that contains various document types as keys and their content as values.
#             If a key named "{verifier_name}" is present in the dictionary, examine its content to verify whether the document is in accordance with the guidelines mentioned in the '../data/template/{doc_name}' document. 
#             Provide a precise response indicating whether the document is valid or not, based on the information in the summary content. DO NOT use any code to verify the content.
#             '''


