import re

from langchain_community.llms import Ollama


class PoemController:
    def __init__(self, model):
        self.model = model
    
    def check_output(self, output, input_text_split):
        line_boolean = None
        word_boolean = None
        
        lines = output.split('\n')
    
        # Filter out any empty strings that might be caused by trailing newlines
        lines = [line for line in lines if line.strip()]
        
        if len(lines) == 5:
            line_boolean = True
        
        else:
            line_boolean = False
        
        output_split = [i.lower() for i in output.split(' ')]
        counter = 0
        for words in input_text_split:
            if words in input_text_split:
                counter = counter + 1
        
        if counter == len(input_text_split):
            word_boolean = True
        
        else:
            word_boolean = False
            
        return line_boolean, word_boolean
            
    
    def get_poem(self, input_text, input_text_split):
        try:
            llm = Ollama(model=self.model, temperature=0)
        except Exception as e:
            return "LLM model not found"
            
        initial_prompt = "generate me a five line poem with words : "
        final_prompt = f"{initial_prompt} '{input_text}'"
        
        output = llm.invoke(final_prompt)
        line_boolean, word_boolean = self.check_output(output, input_text_split)
        
        print(output)
        print(line_boolean, word_boolean)
        
        if line_boolean == False:
            while line_boolean is False:
                final_prompt = final_prompt + '. The total number of lines must be five'
                output = llm.invoke(final_prompt)
                line_boolean, word_boolean = self.check_output(output, input_text_split)
        
        if word_boolean == False:
            while word_boolean is False:
                final_prompt = final_prompt + '. Poem must contains defined words'
                output = llm.invoke(final_prompt)
                line_boolean, word_boolean = self.check_output(output, input_text_split)
                
        return output
                
    def input_preprocess(self, input_text):
        sentence_list = [i.lower() for i in input_text.split(',')]
        return sentence_list

    def generate_poem(self, input_text):
        input_text_split = self.input_preprocess(input_text)
        poem = self.get_poem(input_text, input_text_split)
        
        return poem

