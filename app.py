#!/usr/bin/env python3
import aws_cdk as cdk

from simple_chatbot.simple_chatbot_stack import SimpleChatbotStack


app = cdk.App()
SimpleChatbotStack(app, "SimpleChatbotStack")

app.synth()
