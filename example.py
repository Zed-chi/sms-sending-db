import argparse
import asyncio

import aioredis

from db import Database


def create_argparser():
    parser = argparse.ArgumentParser(
        description="Redis database usage example"
    )
    parser.add_argument(
        "--address",
        action="store",
        dest="redis_uri",
        help="Redis URI",
    )
    parser.add_argument(
        "--password",
        action="store",
        dest="redis_password",
        help="Redis db password",
    )

    return parser


async def main():
    parser = create_argparser()
    args = parser.parse_args()

    redis = await aioredis.from_url(
        args.redis_uri,
        password=args.redis_password,
        encoding="utf-8",
    )

    try:

        db = Database(redis)

        sms_id = "1"

        phones = [
            "+7 999 519 05 57",
            "911",
            "112",
        ]
        text = "Вечером будет шторм!"

        await db.add_sms_mailing(sms_id, phones, text)

        sms_ids = await db.list_sms_mailings()
        print("Registered mailings ids", sms_ids)

        pending_sms_list = await db.get_pending_sms_list()
        print("pending:")
        print(pending_sms_list)

        await db.update_sms_status_in_bulk(
            [
                # [sms_id, phone_number, status]
                [sms_id, "112", "failed"],
                [sms_id, "911", "pending"],
                [sms_id, "+7 999 519 05 57", "delivered"],
                # following statuses are available: failed, pending, delivered
            ]
        )

        pending_sms_list = await db.get_pending_sms_list()
        print("pending:")
        print(pending_sms_list)

        sms_mailings = await db.get_sms_mailings("1")
        print("sms_mailings")
        print(sms_mailings)

        async def send():
            while True:
                await asyncio.sleep(1)
                await redis.publish("updates", sms_id)

        async def listen():
            psub = redis.pubsub()
            async with psub as channel:
                await channel.subscribe("updates")

                while True:
                    raw_message = await channel.get_message(
                        ignore_subscribe_messages=True
                    )

                    if raw_message:
                        raw_data = raw_message.get("data", None)
                        data = raw_data.decode()
                        print("Got message:", data)

        await asyncio.gather(send(), listen())

    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(main())
