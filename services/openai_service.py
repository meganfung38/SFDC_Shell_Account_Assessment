import openai
from config.config import Config

# configure openAI access 
openai.api_key = Config.OPENAI_API_KEY
client = openai.OpenAI()  # creating client instance 

def test_openai_connection():
    """Test OpenAI connection by listing available models"""
    try:
        models = client.models.list()
        model_list = list(models)
        
        if len(model_list) > 0:
            return True, f"OpenAI connection successful - Found {len(model_list)} available models"
        else:
            return False, "OpenAI connection failed - No models available"
            
    except Exception as e:
        return False, f"OpenAI connection failed: {str(e)}"

def test_openai_completion(prompt="Hello! Please respond with 'OpenAI connection test successful.'"):
    """Test OpenAI completion generation"""
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        
        return completion.choices[0].message.content, "OpenAI completion test successful"
        
    except Exception as e:
        return None, f"OpenAI completion test failed: {str(e)}"

def ask_openai(openai_client, system_prompt, user_prompt):
    """calls openai"""
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return completion.choices[0].message.content
    # debugging
    except Exception as openai_error:
        return f"Unexpected error: {openai_error}"

def get_openai_config():
    """Get OpenAI configuration information"""
    return {
        "model": Config.OPENAI_MODEL,
        "max_tokens": Config.OPENAI_MAX_TOKENS,
        "api_key_configured": bool(Config.OPENAI_API_KEY)
    }