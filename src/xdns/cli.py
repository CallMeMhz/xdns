"""命令行接口"""

import os
import click
from rich.console import Console
from rich.table import Table

from .client import DNSClient

console = Console()

# 默认服务商
DEFAULT_PROVIDER = os.environ.get("DNS_PROVIDER", "aliyun")


def get_client(provider: str) -> DNSClient:
    """获取 DNS 客户端"""
    try:
        return DNSClient(provider=provider)
    except ValueError as e:
        console.print(f"[red]错误: {e}[/red]")
        raise SystemExit(1)


@click.group()
@click.version_option()
@click.option(
    "-p", "--provider",
    default=DEFAULT_PROVIDER,
    envvar="DNS_PROVIDER",
    help=f"DNS 服务商 (默认: {DEFAULT_PROVIDER})",
)
@click.pass_context
def main(ctx, provider: str):
    """DNS Hero - DNS 解析管理工具

    支持阿里云、Cloudflare、DNSPod 等多种服务商
    """
    ctx.ensure_object(dict)
    ctx.obj["provider"] = provider


@main.command()
@click.argument("domain")
@click.option("-t", "--type", "record_type", default=None, help="筛选记录类型")
@click.pass_context
def list(ctx, domain: str, record_type: str):
    """列出域名的所有解析记录

    例如: dns list example.com
    """
    client = get_client(ctx.obj["provider"])

    try:
        records = client.list_records(domain, record_type=record_type)
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise SystemExit(1)

    if not records:
        console.print(f"[yellow]域名 {domain} 没有解析记录[/yellow]")
        return

    table = Table(title=f"{domain} 解析记录")
    table.add_column("名称", style="cyan")
    table.add_column("类型", style="green")
    table.add_column("记录值", style="white")
    table.add_column("TTL", style="yellow")

    for r in records:
        table.add_row(
            r["name"],
            r["type"],
            r["content"],
            str(r["ttl"]) if r["ttl"] else "-",
        )

    console.print(table)


@main.command()
@click.argument("full_domain")
@click.argument("value")
@click.option("-t", "--type", "record_type", default="A", help="记录类型 (默认: A)")
@click.pass_context
def add(ctx, full_domain: str, value: str, record_type: str):
    """添加解析记录

    例如:
        dns add www.example.com 1.2.3.4
        dns add blog.example.com cdn.example.com -t CNAME
    """
    client = get_client(ctx.obj["provider"])
    domain, name = client.parse_domain(full_domain)

    console.print(f"[cyan]正在添加解析记录...[/cyan]")
    console.print(f"  域名: {domain}")
    console.print(f"  名称: {name}")
    console.print(f"  类型: {record_type}")
    console.print(f"  记录值: {value}")

    try:
        result = client.add_record(full_domain, value, record_type)
        if result:
            console.print(f"[green]✓ 添加成功！[/green]")
        else:
            console.print(f"[red]✗ 添加失败[/red]")
            raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise SystemExit(1)


@main.command()
@click.argument("full_domain")
@click.option("-t", "--type", "record_type", default="A", help="记录类型 (默认: A)")
@click.pass_context
def delete(ctx, full_domain: str, record_type: str):
    """删除解析记录

    例如:
        dns delete www.example.com
        dns delete www.example.com -t AAAA
    """
    client = get_client(ctx.obj["provider"])

    console.print(f"[cyan]正在删除 {full_domain} 的 {record_type} 记录...[/cyan]")

    try:
        result = client.delete_record(full_domain, record_type)
        if result:
            console.print(f"[green]✓ 删除成功！[/green]")
        else:
            console.print(f"[red]✗ 未找到记录或删除失败[/red]")
            raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise SystemExit(1)


@main.command()
@click.argument("full_domain")
@click.argument("value")
@click.option("-t", "--type", "record_type", default="A", help="记录类型 (默认: A)")
@click.pass_context
def update(ctx, full_domain: str, value: str, record_type: str):
    """更新解析记录（不存在则创建）

    例如:
        dns update www.example.com 5.6.7.8
        dns update www.example.com newcdn.example.com -t CNAME
    """
    client = get_client(ctx.obj["provider"])

    console.print(f"[cyan]正在更新 {full_domain} 的 {record_type} 记录...[/cyan]")

    try:
        success, is_new = client.update_or_create(full_domain, value, record_type)
        if success:
            if is_new:
                console.print(f"[green]✓ 记录不存在，已创建！[/green]")
            else:
                console.print(f"[green]✓ 更新成功！[/green]")
        else:
            console.print(f"[red]✗ 操作失败[/red]")
            raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        raise SystemExit(1)


# 添加别名
main.add_command(delete, name="del")
main.add_command(delete, name="rm")
main.add_command(update, name="set")


if __name__ == "__main__":
    main()
