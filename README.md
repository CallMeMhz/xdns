# xdns

DNS 解析管理命令行工具，基于 dns-lexicon，支持多种 DNS 服务商。

## 安装

```bash
# 从 GitHub 安装（支持阿里云）
uv tool install "xdns[aliyun] @ git+https://github.com/callmemhz/xdns.git"

# 或本地安装
cd xdns
uv tool install ".[aliyun]"
```

## 配置

### 阿里云

```bash
export DNS_PROVIDER="aliyun"  # 可选，默认就是 aliyun
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
```

### Cloudflare

```bash
export DNS_PROVIDER="cloudflare"
export CLOUDFLARE_API_TOKEN="your-api-token"
```

### DNSPod

```bash
export DNS_PROVIDER="dnspod"
export DNSPOD_API_TOKEN="your-api-token"
```

## 使用

```bash
# 列出所有解析记录
xdns list example.com

# 只列出 A 记录
xdns list example.com -t A

# 添加 A 记录
xdns add www.example.com 1.2.3.4

# 添加 CNAME 记录
xdns add blog.example.com cdn.example.com -t CNAME

# 更新记录（不存在则创建）
xdns update www.example.com 5.6.7.8
xdns set www.example.com 5.6.7.8  # 别名

# 删除记录
xdns del www.example.com
xdns rm www.example.com -t AAAA

# 指定服务商
xdns -p cloudflare list example.com
```

## 支持的服务商

通过 dns-lexicon 支持 60+ DNS 服务商，常用的包括：

- aliyun (阿里云)
- cloudflare
- dnspod (腾讯云)
- godaddy
- namecheap
- route53 (AWS)
- ...

完整列表见 [dns-lexicon 文档](https://dns-lexicon.readthedocs.io/en/latest/configuration_reference.html)

## License

MIT
