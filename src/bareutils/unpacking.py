"""Unpackers"""

from email.parser import BytesFeedParser
from email.message import Message
from typing import List, Tuple, Union

from baretypes import Content

MessageParams = List[Tuple[str, str]]
MessagePayload = Union[List[Message], str, bytes, None]

async def unpack_multipart_form_data(
        content_type: bytes,
        content: Content
) -> List[Tuple[MessageParams, MessagePayload]]:
    """Unpack multipart form data

    :param content_type: The 'content-type' header
    :type content_type: bytes
    :param content: The content to parse.
    :type content: Content
    :raises AssertionError: When the problems were found with the data
    :return: The form and files
    :rtype: List[Tuple[MessageParams, MessagePayload]]
    """
    # Create the parser and prime it with the content
    # type.
    parser = BytesFeedParser()
    parser.feed(b'Content-Type: ') # type: ignore[arg-type]
    parser.feed(content_type) # type: ignore[arg-type]
    parser.feed(b'\r\n\r\n') # type: ignore[arg-type]

    # Feed the content to the parser.
    async for buf in content:
        parser.feed(buf)
    msg = parser.close()

    assert msg is not None, "The parser should return a message"
    assert msg.is_multipart(), "The message should be a multipart message"
    assert not msg.defects, "The message should not have defects"

    msg_payload = msg.get_payload()
    assert msg_payload is not None, "The message payload should not be empty"

    data: List[Tuple[MessageParams, MessagePayload]] = []
    for msg_part in msg_payload:
        assert isinstance(msg_part, Message), "A message part should also be a message"
        assert not msg_part.is_multipart(), "A message part should not be multipart"
        assert not msg_part.defects, "A message part should not have defects"

        content_disposition = msg_part.get_params(header='content-disposition')
        assert content_disposition, "A message part should have a content-disposition header"

        part_payload: MessagePayload = msg_part.get_payload(decode=True)
        data.append(
            (content_disposition, part_payload)
        )

    return data
