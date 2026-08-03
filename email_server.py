from flask import Flask, jsonify, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel, Field

# Import native Ollama components
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider

app = Flask(__name__)

# 1. Point to your local Ollama copy
local_model_1 = OllamaModel(
    model_name="qwen3.5:4b",
    provider=OllamaProvider(base_url="http://localhost:11434/v1")
)

# 2. Keep the Pydantic Payload layout for validation
class EmailPayload(BaseModel):
    to_email: str = Field(description="The recipient's email address")
    subject: str = Field(description="The subject line of the email")
    body: str = Field(default="", description="The full text body of the email")

# 3. Configure the Agent
email_agent = Agent(
    model=local_model_1,
    output_type=EmailPayload,
)

@email_agent.system_prompt
def provide_email_agent_prompt() -> str:
    return "### You are an Email Agent. Your task is to generate a structured email payload based on the user's prompt. ###\n\nPlease provide the following information in JSON format:\n- to_email: The recipient's email address\n- subject: The subject line of the email\n- body: The full text body of the email\n\nEnsure that the output is valid JSON and adheres to the EmailPayload structure."

# 4. Standard Email dispatch routine
def execute_send_email(payload: EmailPayload) -> str:
    sender_email = "savioseelam310@gmail.com"
    sender_password = "ewut ubkb amaj xepb"

    if not sender_email or not sender_password:
        return "Error: Missing credentials."

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = payload.to_email
        msg["Subject"] = payload.subject
        msg.attach(MIMEText(payload.body, "plain"))

        server.sendmail(sender_email, payload.to_email, msg.as_string())
        server.quit()
        return f"Success: Email sent to {payload.to_email}!"
    except Exception as e:
        return f"Error: Failed to send email. Details: {str(e)}"

# 5. API Endpoint for Node.js to call
@app.route('/api/send-email-agent', methods=['POST'])
def run_email_agent():
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required"}), 400

    try:
        # Run pydantic-ai agent synchronously
        result = email_agent.run_sync(prompt)
        payload = result.output 
        
        # Dispatch email
        status_message = execute_send_email(payload)
        
        return jsonify({
            "status": "success",
            "details": {
                "to": payload.to_email,
                "subject": payload.subject,
                "body": payload.body
            },
            "result": status_message
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)