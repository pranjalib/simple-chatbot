import aws_cdk as core
import aws_cdk.assertions as assertions

from simple_chatbot.simple_chatbot_stack import SimpleChatbotStack

# example tests. To run these tests, uncomment this file along with the example
# resource in simple_chatbot/simple_chatbot_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SimpleChatbotStack(app, "simple-chatbot")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
