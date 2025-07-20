"""
测试 LifeSmartClient 类的核心功能。
"""

import hashlib
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.lifesmart.exceptions import LifeSmartAPIError, LifeSmartAuthError
from custom_components.lifesmart.lifesmart_client import LifeSmartClient


@pytest.fixture
def client(hass):
    return LifeSmartClient(
        hass,
        region="cn2",
        appkey="mock_appkey",
        apptoken="mock_apptoken",
        usertoken="mock_usertoken",
        userid="mock_userid",
    )


@pytest.mark.asyncio
async def test_get_all_device_async_success(client):
    """测试成功获取所有设备。"""
    mock_response = {
        "code": 0,
        "message": [{"agt": "hub1", "me": "dev1"}, {"agt": "hub1", "me": "dev2"}],
    }
    with patch(
        "custom_components.lifesmart.lifesmart_client.LifeSmartClient._post_and_parse",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_post:
        devices = await client.get_all_device_async()
        mock_post.assert_called_once()
        call_args = mock_post.call_args[0]
        assert "api.EpGetAll" in call_args[0]  # URL
        assert call_args[1]["method"] == "EpGetAll"
        assert len(devices) == 2
        assert devices[0]["me"] == "dev1"


@pytest.mark.asyncio
async def test_api_call_failure_raises_exception(client):
    """测试API返回非零错误码时抛出异常。"""
    mock_response = {"code": 10004, "message": "sign error"}
    with patch(
        "custom_components.lifesmart.lifesmart_client.LifeSmartClient._post_and_parse",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        with pytest.raises(LifeSmartAuthError) as excinfo:
            await client.get_all_device_async()
        assert excinfo.value.code == 10004

        mock_response["code"] = 10009  # 另一个错误码
        with pytest.raises(LifeSmartAPIError) as excinfo:
            await client.get_all_device_async()
        assert excinfo.value.code == 10009


def test_signature_generation(client):
    """测试签名生成逻辑。"""
    sdata = "method:EpGetAll,time:1672502400,userid:mock_userid,usertoken:mock_usertoken,appkey:mock_appkey,apptoken:mock_apptoken"
    expected_sign = hashlib.md5(sdata.encode("utf-8")).hexdigest()
    generated_sign = client.get_signature(sdata)
    assert generated_sign == expected_sign


@pytest.mark.asyncio
async def test_turn_on_light_switch_async(client):
    """测试开灯/开关方法是否构建了正确的API调用。"""
    with patch(
        "custom_components.lifesmart.lifesmart_client.LifeSmartClient._async_call_api",
        new_callable=AsyncMock,
    ) as mock_call_api:
        await client.turn_on_light_switch_async("L1", "hub1", "dev1")
        mock_call_api.assert_called_with(
            "EpSet",
            {"agt": "hub1", "me": "dev1", "idx": "L1", "type": "0x81", "val": 1},
        )
