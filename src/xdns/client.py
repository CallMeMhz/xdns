"""DNS API 客户端 (基于 dns-lexicon)"""

import os
from typing import Optional

from lexicon.client import Client
from lexicon.config import ConfigResolver


class DNSClient:
    """DNS 客户端封装，支持多种服务商"""

    PROVIDER_ENV_MAP = {
        "aliyun": {
            "auth_key_id": "ALIYUN_ACCESS_KEY_ID",
            "auth_secret": "ALIYUN_ACCESS_KEY_SECRET",
        },
        "cloudflare": {
            "auth_token": "CLOUDFLARE_API_TOKEN",
        },
        "dnspod": {
            "auth_token": "DNSPOD_API_TOKEN",
        },
    }

    def __init__(
        self,
        provider: str = "aliyun",
        **credentials,
    ):
        self.provider = provider
        self.credentials = credentials

        # 如果没传凭证，从环境变量读取
        if not credentials and provider in self.PROVIDER_ENV_MAP:
            env_map = self.PROVIDER_ENV_MAP[provider]
            for key, env_name in env_map.items():
                value = os.environ.get(env_name)
                if value:
                    self.credentials[key] = value

        if not self.credentials:
            env_vars = self.PROVIDER_ENV_MAP.get(provider, {})
            env_list = "\n".join(f"  {v}" for v in env_vars.values())
            raise ValueError(
                f"请设置 {provider} 的认证环境变量：\n{env_list}"
            )

    @staticmethod
    def parse_domain(full_domain: str) -> tuple[str, str]:
        """
        解析完整域名，返回 (主域名, 主机记录)
        例如: www.example.com -> (example.com, www)
              sub.www.example.com -> (example.com, sub.www)
              example.com -> (example.com, @)
        """
        parts = full_domain.rstrip(".").split(".")

        if len(parts) < 2:
            raise ValueError(f"无效的域名格式: {full_domain}")

        # 处理 .com.cn, .net.cn, .org.cn 等后缀
        tld = parts[-1]
        sld = parts[-2]

        if tld == "cn" and sld in ("com", "net", "org", "gov", "edu"):
            # 三级域名后缀
            if len(parts) < 3:
                return full_domain, "@"
            domain = f"{parts[-3]}.{sld}.{tld}"
            if len(parts) == 3:
                rr = "@"
            else:
                rr = ".".join(parts[:-3])
        else:
            # 普通二级域名后缀
            domain = f"{sld}.{tld}"
            if len(parts) == 2:
                rr = "@"
            else:
                rr = ".".join(parts[:-2])

        return domain, rr

    def _get_client(self, domain: str) -> Client:
        """获取 lexicon 客户端"""
        config = ConfigResolver().with_dict({
            "provider_name": self.provider,
            "domain": domain,
            self.provider: self.credentials,
        })
        return Client(config)

    def list_records(
        self, domain: str, record_type: Optional[str] = None, name: Optional[str] = None
    ) -> list[dict]:
        """列出域名的所有解析记录"""
        client = self._get_client(domain)

        with client as c:
            records = c.list_records(rtype=record_type, name=name)

        return [
            {
                "id": r.get("id"),
                "name": r.get("name", ""),
                "type": r.get("type", ""),
                "content": r.get("content", ""),
                "ttl": r.get("ttl", ""),
            }
            for r in records
        ]

    def add_record(
        self,
        full_domain: str,
        content: str,
        record_type: str = "A",
        ttl: Optional[int] = None,
    ) -> bool:
        """添加解析记录"""
        domain, name = self.parse_domain(full_domain)
        client = self._get_client(domain)

        # lexicon 需要完整的 name
        if name == "@":
            full_name = domain
        else:
            full_name = f"{name}.{domain}"

        with client as c:
            return c.create_record(rtype=record_type, name=full_name, content=content)

    def find_record(
        self, full_domain: str, record_type: str = "A"
    ) -> Optional[dict]:
        """查找指定的解析记录"""
        domain, name = self.parse_domain(full_domain)

        if name == "@":
            full_name = domain
        else:
            full_name = f"{name}.{domain}"

        records = self.list_records(domain, record_type=record_type, name=full_name)
        return records[0] if records else None

    def delete_record(
        self, full_domain: str, record_type: str = "A", content: Optional[str] = None
    ) -> bool:
        """删除解析记录"""
        domain, name = self.parse_domain(full_domain)
        client = self._get_client(domain)

        if name == "@":
            full_name = domain
        else:
            full_name = f"{name}.{domain}"

        with client as c:
            return c.delete_record(rtype=record_type, name=full_name, content=content)

    def update_record(
        self,
        full_domain: str,
        content: str,
        record_type: str = "A",
    ) -> bool:
        """更新解析记录"""
        domain, name = self.parse_domain(full_domain)
        client = self._get_client(domain)

        if name == "@":
            full_name = domain
        else:
            full_name = f"{name}.{domain}"

        with client as c:
            return c.update_record(rtype=record_type, name=full_name, content=content)

    def update_or_create(
        self,
        full_domain: str,
        content: str,
        record_type: str = "A",
    ) -> tuple[bool, bool]:
        """更新解析记录，不存在则创建。返回 (成功, 是否为新建)"""
        record = self.find_record(full_domain, record_type)

        if record:
            success = self.update_record(full_domain, content, record_type)
            return success, False
        else:
            success = self.add_record(full_domain, content, record_type)
            return success, True
