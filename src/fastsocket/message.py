import json
import uuid

class Message:
    """
    Represents a message used for communication between client and server.

    Attributes:
        uuid (int): Unique identifier for the message.
        code (str): Message code indicating the type or purpose of the message.
        data (dict): Payload data of the message.
    """

    def __init__(self, code: str, uuid: int = int(uuid.uuid4()),  data: dict = {}) -> None:
        """
        Initialize a Message instance.

        Args:
            uuid (int): Unique identifier for the message.
            code (str): Message code indicating the type or purpose of the message.
            data (dict): Payload data of the message.
        """
        self.uuid = uuid
        self.code = code
        self.data = data

    @classmethod
    def from_dict(cls, dict: dict):
        """
        Create a Message instance from a dictionary.

        Args:
            dict (dict): A dictionary containing the message attributes.

        Returns:
            Message: A new Message instance.
        """
        obj = cls(**dict)
        return obj
    
    @classmethod
    def from_json(cls, string: str):
        """
        Create a Message instance from a JSON string.

        Args:
            string (str): A JSON string representing the message.

        Returns:
            Message: A new Message instance.
        """
        obj = cls(**json.loads(string))
        return obj

    def to_dict(self) -> dict:
        """
        Convert the Message instance to a dictionary.

        Returns:
            dict: A dictionary representation of the Message.
        """
        return {
            "uuid": self.uuid,
            "code": self.code,
            "data": self.data,
        }
    
    def to_json(self) -> str:
        """
        Convert the Message instance to a JSON string.

        Returns:
            str: A JSON string representation of the Message.
        """
        return json.dumps(self.to_dict())