# -*- coding: utf-8 -*-
import re,urllib
from shejiao.settings import *
from django.shortcuts import render_to_response
from django.template import context
from django.core.paginator import Paginator, InvalidPage

def tiny_url(url):
    u"""
    summary:
        将url转换成tinyurl
    author:
        Jason Lee <huacnlee@gmail.com>
    """
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = urllib.urlopen(apiurl + url).read()
    return tinyurl

def content_tiny_url(content):
    u"""
    summary:
        让消息里面的连接转换成更短的Tinyurl
    author:
        Jason Lee <huacnlee@gmail.com>
    """
    
    regex_url = r'http:\/\/([\w.]+\/?)\S*'
    for match in re.finditer(regex_url, content):
        url = match.group(0)
        content = content.replace(url,tiny_url(url))
    
    return content

def substr(content, length,add_dot=True):
    u"""
    summary:
        字符串截取
    author:
        Jason Lee <huacnlee@gmail.com>
    """
    if(len(content) > length):
        content = content[:length]
        if(add_dot):
            content = content[:len(content)-3] + '...'
    return content

