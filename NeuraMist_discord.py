import os
import asyncio
import logging
import json
import boto3
import uuid
import discord
import random
import subprocess
import pyautogui
from dotenv import load_dotenv
import botocore.exceptions  # Import botocore.exceptions

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID')
BEDROCK_AGENT_ALIAS = os.getenv('BEDROCK_AGENT_ALIAS')
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE')
SNOWFLAKE_SCHEMA = os.getenv('SNOWFLAKE_SCHEMA')

# Debug prints to verify environment variables
logger.info(f"DISCORD_BOT_TOKEN: {DISCORD_BOT_TOKEN}")
logger.info(f"AWS_REGION: {AWS_REGION}")
logger.info(f"BEDROCK_AGENT_ID: {BEDROCK_AGENT_ID}")
logger.info(f"BEDROCK_AGENT_ALIAS: {BEDROCK_AGENT_ALIAS}")
logger.info(f"SNOWFLAKE_ACCOUNT: {SNOWFLAKE_ACCOUNT}")
logger.info(f"SNOWFLAKE_USER: {SNOWFLAKE_USER}")
logger.info(f"SNOWFLAKE_WAREHOUSE: {SNOWFLAKE_WAREHOUSE}")
logger.info(f"SNOWFLAKE_DATABASE: {SNOWFLAKE_DATABASE}")
logger.info(f"SNOWFLAKE_SCHEMA: {SNOWFLAKE_SCHEMA}")

class BedrockAgent:
    def __init__(self):
        if not BEDROCK_AGENT_ID or not BEDROCK_AGENT_ALIAS:
            raise ValueError("BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS environment variables must be set")
        self.client = boto3.client(
            'bedrock-agent-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

    async def invoke_agent(self, prompt):
        session_id = str(uuid.uuid4())  # Generate a unique session ID
        try:
            response = self.client.invoke_agent(
                agentId=BEDROCK_AGENT_ID,
                agentAliasId=BEDROCK_AGENT_ALIAS,
                sessionId=session_id,
                inputText=prompt
            )

            full_response = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        full_response += chunk['bytes'].decode('utf-8')

            return full_response
        except botocore.exceptions.ClientError as e:
            logger.error(f"AWS ClientError invoking Bedrock agent: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error invoking Bedrock agent: {str(e)}", exc_info=True)
            raise

class SnowflakeAgent:
    def __init__(self):
        import snowflake.connector
        if not SNOWFLAKE_ACCOUNT:
            raise ValueError("SNOWFLAKE_ACCOUNT environment variable is not set")
        self.conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )

    def execute_query(self, query):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            raise

    def create_table(self, table_name, columns):
        try:
            cursor = self.conn.cursor()
            column_defs = ", ".join([f"{col_name} {col_type}" for col_name, col_type in columns.items()])
            query = f"CREATE TABLE {table_name} ({column_defs})"
            cursor.execute(query)
            cursor.close()
            return f"Table {table_name} created successfully."
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}", exc_info=True)
            raise

    def insert_data(self, table_name, data):
        try:
            cursor = self.conn.cursor()
            column_names = ", ".join(data.keys())
            values = ", ".join([f"'{value}'" for value in data.values()])
            query = f"INSERT INTO {table_name} ({column_names}) VALUES ({values})"
            cursor.execute(query)
            self.conn.commit()
            cursor.close()
            return f"Data inserted into table {table_name} successfully."
        except Exception as e:
            logger.error(f"Error inserting data: {str(e)}", exc_info=True)
            raise

    def describe_table(self, table_name):
        try:
            cursor = self.conn.cursor()
            query = f"DESCRIBE TABLE {table_name}"
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Error describing table: {str(e)}", exc_info=True)
            raise

class DiscordSnowflakeBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bedrock_agent = BedrockAgent()
        self.snowflake_agent = SnowflakeAgent()
        self.statuses = [
            "Ask me anything!",
            "Ready to help with Snowflake and AWS",
            "Powered by Snowflake Cortex and AWS Bedrock",
            "Snowflaking around...",
            "AWS Bedrock-ing...",
            "Checking Snowflake facts...",
            "AWS Bedrock insights..."
        ]
        self.random_actions = [
            "Did you know? Snowflake supports semi-structured data!",
            "Fun Fact: AWS Bedrock can generate text, images, and more!",
            "Tip: Use !help to see available commands.",
            "Snowflake is a powerful data platform!",
            "AWS Bedrock makes AI accessible to everyone!"
        ]

    async def on_ready(self):
        logger.info(f'Logged in as {self.user}')
        await self.update_status()
        self.loop.create_task(self.perform_random_actions())
        self.loop.create_task(self.change_status_randomly())

    async def update_status(self):
        status = random.choice(self.statuses)
        await self.change_presence(activity=discord.Game(name=status))

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!chat'):
            await self.handle_chat_command(message)
        elif message.content.startswith('!snowflake'):
            await self.handle_snowflake_command(message)
        elif message.content.startswith('!help'):
            await self.handle_help_command(message)
        elif message.content.startswith('!random'):
            await self.perform_random_action(message.channel)
        elif message.content.startswith('!start'):
            args = message.content.split(' ', 1)
            if len(args) < 2:
                await message.channel.send("Usage: !start <application>")
                return
            application = args[1]
            await self.start_application(message.channel, application)
        elif message.content.startswith('!type'):
            args = message.content.split(' ', 2)
            if len(args) < 3:
                await message.channel.send("Usage: !type <application> <text>")
                return
            application = args[1]
            text = args[2]
            await self.type_in_application(message.channel, application, text)
        elif message.content.startswith('!create_table'):
            args = message.content.split(' ', 2)
            if len(args) < 3:
                await message.channel.send("Usage: !create_table <table_name> <column1_name:column1_type,column2_name:column2_type,...>")
                return
            table_name = args[1]
            columns_str = args[2]
            columns = dict(item.split(':') for item in columns_str.split(','))
            await self.create_table(message.channel, table_name, columns)
        elif message.content.startswith('!insert_data'):
            args = message.content.split(' ', 2)
            if len(args) < 3:
                await message.channel.send("Usage: !insert_data <table_name> <column1_name:value1,column2_name:value2,...>")
                return
            table_name = args[1]
            data_str = args[2]
            data = dict(item.split(':') for item in data_str.split(','))
            await self.insert_data(message.channel, table_name, data)
        elif message.content.startswith('!describe_table'):
            args = message.content.split(' ', 1)
            if len(args) < 2:
                await message.channel.send("Usage: !describe_table <table_name>")
                return
            table_name = args[1]
            await self.describe_table(message.channel, table_name)

    async def handle_chat_command(self, message):
        args = message.content.split(' ', 1)
        if len(args) < 2:
            await message.channel.send("Usage: !chat <prompt>")
            return
        prompt = args[1]
        try:
            response = await self.bedrock_agent.invoke_agent(prompt)
            await message.channel.send(f"AWS Bedrock AI says: {response}")
        except botocore.exceptions.ClientError as e:
            logger.error(f"AWS ClientError invoking Bedrock agent: {str(e)}", exc_info=True)
            await message.channel.send(f"Failed to get response from AWS Bedrock: {str(e)}")
        except Exception as e:
            logger.error(f"Error invoking Bedrock agent: {str(e)}", exc_info=True)
            await message.channel.send(f"Failed to get response from AWS Bedrock: {str(e)}")

    async def handle_snowflake_command(self, message):
        args = message.content.split(' ', 1)
        if len(args) < 2:
            await message.channel.send("Usage: !snowflake <query>")
            return
        query = args[1]
        try:
            result = self.snowflake_agent.execute_query(query)
            await message.channel.send(f"Snowflake Query Result: {result}")
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            await message.channel.send(f"Failed to execute Snowflake query: {str(e)}")

    async def handle_help_command(self, message):
        help_message = (
            "**Available Commands:**\n"
            "!chat <prompt> - Get a response from the MistralRAG AI Agent.\n"
            "!snowflake <query> - Execute a SQL query on Snowflake.\n"
            "!create_table <table_name> <column1_name:column1_type,column2_name:column2_type,...> - Create a new table in Snowflake.\n"
            "!insert_data <table_name> <column1_name:value1,column2_name:value2,...> - Insert data into a Snowflake table.\n"
            "!describe_table <table_name> - Describe a Snowflake table.\n"
            "!help - Display this help message.\n"
            "!random - Perform a random action.\n"
            "!start <application> - Start a Windows application (e.g., calculator, chrome).\n"
            "!type <application> <text> - Type text into a started application.\n"
        )
        await message.channel.send(help_message)

    async def perform_random_actions(self):
        while True:
            await asyncio.sleep(random.randint(300, 600))  # Sleep for a random interval between 5 and 10 minutes
            action = random.choice(self.random_actions)
            for channel in self.get_all_channels():
                if isinstance(channel, discord.TextChannel):
                    await channel.send(action)
                    break

    async def change_status_randomly(self):
        while True:
            await asyncio.sleep(random.randint(60, 120))  # Sleep for a random interval between 1 and 2 minutes
            status = random.choice(self.statuses)
            await self.change_presence(activity=discord.Game(name=status))

    async def perform_random_action(self, channel):
        action = random.choice(self.random_actions)
        await channel.send(action)

    async def start_application(self, channel, application):
        try:
            if application.lower() == "calculator":
                subprocess.Popen(["calc"])
                await channel.send("Calculator has been started.")
            elif application.lower() == "chrome":
                subprocess.Popen(["chrome"])
                await channel.send("Chrome has been started.")
            else:
                await channel.send("Unknown application. Use 'calculator' or 'chrome'.")
        except Exception as e:
            logger.error(f"Error starting application: {str(e)}", exc_info=True)
            await channel.send(f"Failed to start application: {str(e)}")

    async def type_in_application(self, channel, application, text):
        try:
            if application.lower() == "calculator":
                await channel.send("Typing in Calculator is not supported.")
            elif application.lower() == "chrome":
                await asyncio.sleep(5)  # Wait for Chrome to open
                pyautogui.typewrite(text)
                await channel.send(f"Typed '{text}' into Chrome.")
            else:
                await channel.send("Unknown application. Use 'chrome'.")
        except Exception as e:
            logger.error(f"Error typing in application: {str(e)}", exc_info=True)
            await channel.send(f"Failed to type in application: {str(e)}")

    async def create_table(self, channel, table_name, columns):
        try:
            result = self.snowflake_agent.create_table(table_name, columns)
            await channel.send(result)
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}", exc_info=True)
            await channel.send(f"Failed to create table: {str(e)}")

    async def insert_data(self, channel, table_name, data):
        try:
            result = self.snowflake_agent.insert_data(table_name, data)
            await channel.send(result)
        except Exception as e:
            logger.error(f"Error inserting data: {str(e)}", exc_info=True)
            await channel.send(f"Failed to insert data: {str(e)}")

    async def describe_table(self, channel, table_name):
        try:
            result = self.snowflake_agent.describe_table(table_name)
            await channel.send(f"Table Description: {result}")
        except Exception as e:
            logger.error(f"Error describing table: {str(e)}", exc_info=True)
            await channel.send(f"Failed to describe table: {str(e)}")

def main():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = DiscordSnowflakeBot(intents=intents)
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()
