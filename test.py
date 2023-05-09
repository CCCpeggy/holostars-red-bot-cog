async def check_video_owner(channel_id: str, video_id: str) -> bool:
    params = {
        "channel_id": channel_id,
        "id": video_id
    }
    # log.debug(params)
    data = await get_http_data("https://holodex.net/api/v2/videos", params)
    # log.debug(data)
    return data and len(data) > 0

async def test():
    print(await check_video_owner("UC2hx0xVkMoHGWijwr_lA01w", "DxHteQ_8dRU"))

import asyncio

asyncio.create_task(test)
