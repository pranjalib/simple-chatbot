import os
from constructs import Construct
from aws_cdk import Duration, Size, Stack
from aws_cdk.aws_iam import (
    Effect,
    Role,
    ManagedPolicy,
    PolicyStatement,
    ServicePrincipal
)
from aws_cdk.aws_lambda import (
    Function,
    Runtime,
    Code
)
from aws_cdk.aws_lex import (
    CfnBot,
    CfnBotAlias
)

class SimpleChatbotStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Lambda

        # Role for execution
        test_lambda_role = Role(
            scope=self,
            id="TestLambdaRole",
            role_name="TestLambdaRole",
            description="IAM Execution role for bot",
            assumed_by=ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[ManagedPolicy.from_aws_managed_policy_name(
                managed_policy_name="service-role/AWSLambdaBasicExecutionRole")
            ]
        )

        lambda_function = Function(
            scope=self,
            id="BotLambda",
            function_name="BotLambda",
            runtime=Runtime.PYTHON_3_8,
            code=Code.from_asset(os.path.join(os.getcwd(),'simple_chatbot/lambda')),
            handler='invoke_lambda.handler',
            timeout=Duration.seconds(60),
            memory_size=2048,
            ephemeral_storage_size=Size.mebibytes(2048),
            role=test_lambda_role
        )

        # Lambda policy to access Lex
        self.lambda_lex_policy = PolicyStatement(
            actions=["lex:GetSession",
                     "lex:RecognizeText",
                     "lex:ListBotAliases",
                     "lex:ListBots",
                     "lex:DeleteSession",
                     "lex:PutSession"],
            effect=Effect.ALLOW,
            resources=["*"]
        )
        lambda_function.add_to_role_policy(self.lambda_lex_policy)

        # Lambda policy for bedrock
        self.lambda_bedrock_policy = PolicyStatement(
            actions=["bedrock:ListFoundationModels",
                    "bedrock:InvokeModel"],
            effect=Effect.ALLOW,
            resources=["*"]
        )
        lambda_function.add_to_role_policy(self.lambda_bedrock_policy)

        # IAM Role for Lex Bot
        lex_iam_role = Role(
            self, "LexBotIAMRole",
            assumed_by=ServicePrincipal("lex.amazonaws.com"),
            managed_policies=[ManagedPolicy.from_aws_managed_policy_name("AmazonLexFullAccess")],
        )
   
        greeting_intent = CfnBot.IntentProperty(
                name="WelcomeIntent",
                sample_utterances=[
                    CfnBot.SampleUtteranceProperty(
                                    utterance="Hi"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="Hello"
                    ),
                ],
                fulfillment_code_hook=CfnBot.FulfillmentCodeHookSettingProperty(
                    enabled=True)
        )
        
        request_towels_intent = CfnBot.IntentProperty(
                name="RequestTowelsIntent",
                sample_utterances=[
                    CfnBot.SampleUtteranceProperty(
                                    utterance="I want to request a towel"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="towels"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="Send number of towels"
                    ),
                ],
                fulfillment_code_hook=CfnBot.FulfillmentCodeHookSettingProperty(
                    enabled=True)
        )

        amenities_intent = CfnBot.IntentProperty(
                name="AmenitiesIntent",
                sample_utterances=[
                    CfnBot.SampleUtteranceProperty(
                                    utterance="Tell me about the amenities"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="amenities"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="is there a pool?"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="do you provide wifi?"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="is parking available?"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="do you serve breakfast?"
                    ),
                    
                ],
                fulfillment_code_hook=CfnBot.FulfillmentCodeHookSettingProperty(
                    enabled=True)
        )

        reservation_intent = CfnBot.IntentProperty(
                name="ReservationIntent",
                sample_utterances=[
                    CfnBot.SampleUtteranceProperty(
                                    utterance="cabana"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="reserve poolside cabana"
                    ),
                    CfnBot.SampleUtteranceProperty(
                                    utterance="is poolside cabana available"
                    ),
                ],
                fulfillment_code_hook=CfnBot.FulfillmentCodeHookSettingProperty(
                    enabled=True)
        )

        fallback_intent = CfnBot.IntentProperty(
            name="FallbackIntent",
            parent_intent_signature="AMAZON.FallbackIntent",
            fulfillment_code_hook=CfnBot.FulfillmentCodeHookSettingProperty(
                enabled=True,
                is_active=True,
            )
        )

        lex_bot_settings = CfnBot.TestBotAliasSettingsProperty(
            bot_alias_locale_settings=[
                CfnBot.BotAliasLocaleSettingsItemProperty(
                    locale_id="en_US",
                    bot_alias_locale_setting=CfnBot.BotAliasLocaleSettingsProperty(
                        enabled=True,
                        code_hook_specification=CfnBot.CodeHookSpecificationProperty(
                            lambda_code_hook=CfnBot.LambdaCodeHookProperty(
                                code_hook_interface_version="1.0",
                                lambda_arn=lambda_function.function_arn,
                            )
                        ),
                    ),
                )
            ],
        )
        
        bot_config = {
            "name": "HotelAmenitiesBot",
            "description": "A bot to answer hotel amenity questions",
            "idle_session_ttl_in_seconds": 300,
            "data_privacy": {"ChildDirected":"false"},
            "role_arn": lex_iam_role.role_arn,
            "auto_build_bot_locales":True,
            "test_bot_alias_settings":lex_bot_settings,
            "bot_locales": [
                CfnBot.BotLocaleProperty(
                    locale_id="en_US",
                    nlu_confidence_threshold=0.4,
                    intents=[greeting_intent, request_towels_intent, amenities_intent, reservation_intent, fallback_intent]
                    )
            ],
        }

        
        # Create the Lex Bot
        lex_chat_bot = CfnBot(self, "HotelAmenitiesBot", **bot_config)
        

        # Alias
        lex_bot_alias = CfnBotAlias(self, 'AtlasLexBotAlias',
            bot_id=lex_chat_bot.ref,
            bot_alias_name="LexBotAlias",
            bot_alias_locale_settings=[
                CfnBotAlias.BotAliasLocaleSettingsItemProperty(
                    bot_alias_locale_setting=CfnBotAlias.BotAliasLocaleSettingsProperty(
                        enabled=True,

                        # the properties below are optional
                        code_hook_specification=CfnBotAlias.CodeHookSpecificationProperty(
                            lambda_code_hook=CfnBotAlias.LambdaCodeHookProperty(
                                code_hook_interface_version="1.0",
                                lambda_arn=lambda_function.function_arn ## lambda arn -- need to fill
                            )
                        )
                    ),
                    locale_id="en_US"
                )]
        )

        lambda_function.add_permission(scope=self, id='Trigger',
                                    principal=ServicePrincipal("lexv2.amazonaws.com"),
                                    action='lambda:InvokeFunction')