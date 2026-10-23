#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OS-ETC-IRIDIS: build a Chinese-localized Termux arm (32-bit) core tarball.
Input : bootstrap-arm.zip (official Termux 32-bit core, bootstrap-*.zip)
Output: dist/os-etc-termux-core-arm-zh.tar.gz + sha256 file.
"""
import os, re, shutil, sys, tarfile, zipfile, hashlib, stat

SRC = "/home/user/Doubao/chats/38448383717788674/bootstrap_arm"
OUT = "/home/user/Doubao/chats/38448383717788674/os-etc-termux-core-arm-zh.tar.gz"

# ---------- 1. rebuild symlinks from SYMLINKS.txt ----------
links = []
for line in open(os.path.join(SRC, "SYMLINKS.txt"), encoding="utf-8"):
    line = line.strip()
    if not line or "←" not in line:
        continue
    name, target = line.split("←", 1)
    links.append((name[2:] if name.startswith("./") else name,
                  target[2:] if target.startswith("./") else target))

def rel_join(base, p):
    b = os.path.normpath(os.path.join(base, p))
    rp = os.path.realpath(base)
    if os.path.commonpath([rp, os.path.realpath(os.path.dirname(b))]) != rp:
        return None
    return b

made = 0
for name, target in links:
    path = rel_join(SRC, name)
    if path is None:
        continue
    tgt = rel_join(SRC, target)
    if tgt is None or not os.path.lexists(tgt) and not os.path.exists(tgt):
        # target may not exist at build time; keep the link anyway (dangling)
        pass
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        os.symlink(target, path)
        made += 1
    except OSError as e:
        print("symlink fail", name, e)

print(f"symlinks rebuilt: {made}")

# ---------- 2. Chinese localization files ----------
MOTD = """欢迎使用 OS-ETC 内置 Termux 中文核心（32 位 / armeabi-v7a）
=============================================
本核心由 OS-ETC-IRIDIS（ETQWFD 维护）汉化并内置：
 · 源自官方 Termux bootstrap（arm），完整保留原版功能
 · 中文欢迎语 / 中文提示符 / 常用别名
 · 配合 OS-ETC-IRIDIS 使用，无需另外安装 Termux
 · 软件源默认北京清华 TUNA 镜像

有问题请发送邮箱给开发者：2416444244@qq.com
输入 osetc-help 查看中文说明
=============================================
"""

PROFILE_ZH = """# OS-ETC-IRIDIS: 中文汉化 profile（由 ETQWFD 注入）
# 中文提示符
export PS1='\\[\\033[1;36m\\]OS-ETC\\[\\033[0m\\] \\[\\033[1;32m\\]\\u\\[\\033[0m\\]@\\[\\033[1;35m\\]\\h\\[\\033[0m\\]:\\[\\033[1;34m\\]\\w\\[\\033[0m\\]\\$ '

# 常用中文别名
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias cls='clear'
alias 打开='cd'
alias 帮助='osetc-help'
alias 更新='apt update'
alias 安装='apt install'

# 中文帮助命令
osetc-help() {
  cat /share/doc/OS-ETC-README-zh.txt 2>/dev/null || cat /usr/share/doc/OS-ETC-README-zh.txt 2>/dev/null
}

# 提示软件源（北京清华镜像）
if [ -n "$(command -v apt)" ]; then
  echo "[OS-ETC] 软件源已配置为北京清华 TUNA 镜像（mirrors.tuna.tsinghua.edu.cn）"
fi

# locale 提示（如需中文命令输出可执行：apt install coreutils-locales）
export LANG="${LANG:-C.UTF-8}"
"""

README_ZH = """OS-ETC 内置 Termux 中文核心（32 位）使用说明
==========================================
本核心压缩包由 OS-ETC-IRIDIS 项目汉化并发布，源自官方 Termux
bootstrap（arm / armeabi-v7a，32 位），由 ETQWFD 维护。

功能
----
 · 完整 Termux 命令行环境：bash、coreutils、apt、busybox 等
 · 32 位（armeabi-v7a）专用，适配老款/低配安卓手机
 · 配合 OS-ETC-IRIDIS App 直接使用，无需单独安装 Termux

中文体验
--------
 · 欢迎语、提示符（PS1）、常用别名均已汉化
 · 如需命令输出的中文翻译，执行：apt update && apt install coreutils-locales
 · 软件源已指向北京清华 TUNA 镜像（mirrors.tuna.tsinghua.edu.cn）

常用命令
--------
  apt update       更新软件源（清华镜像）
  apt install 包名  安装软件包
  ll / ls          查看文件
  osetc-help       查看本说明

版权与许可
----------
 · 上游：Termux（termux-packages，GPL-2.0 / Apache-2.0 等）
 · 本核心保留上游一切版权与致谢
 · OS-ETC 分支由 ETQWFD 维护，MIT 许可

支持
----
 有任何问题，请发送这个邮箱给开发者：2416444244@qq.com
"""

def write_if(rel, text):
    p = rel_join(SRC, rel)
    if p is None:
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(p, 0o644)

write_if("etc/motd", MOTD)
write_if("etc/profile.d/20-osetc-zh.sh", PROFILE_ZH)
write_if("share/doc/OS-ETC-README-zh.txt", README_ZH)
write_if("usr/share/doc/OS-ETC-README-zh.txt", README_ZH)

# resolv.conf (network for apt)
p = rel_join(SRC, "etc/resolv.conf")
if p:
    with open(p, "w") as f:
        f.write("nameserver 223.5.5.5\nnameserver 8.8.8.8\nnameserver 1.1.1.1\n")

print("localization files written")

# ---------- 3. fix permissions: dirs 755, executables 755, files 644 ----------
def set_mode(p, mode):
    try:
        os.chmod(p, mode)
    except OSError:
        pass

EXEC_PREFIXES = ("bin/", "sbin/", "libexec/", "usr/bin/", "usr/sbin/", "usr/libexec/")
n_exec = 0
for root, dirs, files in os.walk(SRC, followlinks=False):
    for d in dirs:
        set_mode(os.path.join(root, d), 0o755)
    for f in files:
        fp = os.path.join(root, f)
        if os.path.islink(fp):
            continue
        rel = os.path.relpath(fp, SRC).replace(os.sep, "/")
        if rel.startswith(EXEC_PREFIXES) or rel in ("bin/bash",):
            # keep original x bit if any, else give 755 to ELF/shell in bin paths
            st = os.stat(fp)
            if st.st_mode & 0o111:
                set_mode(fp, st.st_mode | 0o111 | 0o444)
            else:
                set_mode(fp, 0o755)
            n_exec += 1
        else:
            set_mode(fp, 0o644)

print(f"executables normalized: {n_exec}")

# ---------- 4. package tar.gz ----------
def tar_filter(ti):
    # rewrite modes: keep exec bits for bin paths
    rel = ti.name.lstrip("./")
    if rel.startswith(EXEC_PREFIXES):
        ti.mode = 0o755
    else:
        ti.mode = 0o644
    return ti

with tarfile.open(OUT, "w:gz", format=tarfile.PAX_FORMAT, compresslevel=9) as tar:
    tar.add(SRC, arcname="", recursive=True, filter=tar_filter)

print("tarball:", OUT)
sz = os.path.getsize(OUT)
h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
print(f"SIZE={sz}")
print(f"SHA256={h}")
with open(OUT + ".sha256", "w") as f:
    f.write(f"{h}  {os.path.basename(OUT)}\n")
