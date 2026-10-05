"""Render the generic initialization workflow (SVG; optional PNG with Pillow)."""
from pathlib import Path
import argparse
import html

W, H = 1600, 1680


def render(output, png=False):
    output.mkdir(parents=True, exist_ok=True)
    svg = []
    canvas = draw = None
    if png:
        from PIL import Image, ImageDraw, ImageFont
        canvas = Image.new('RGB', (W, H), '#f3f6fb'); draw = ImageDraw.Draw(canvas)
        latin = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        chinese = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
    def rect(x,y,w,h,fill,stroke=None):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
        if draw: draw.rounded_rectangle((x,y,x+w,y+h),radius=14,fill=fill,outline=stroke)
    def text(x,y,value,size=20,color='#18273e'):
        svg.append(f'<text x="{x}" y="{y+size}" font-size="{size}" fill="{color}">{html.escape(value)}</text>')
        if draw:
            px=x
            for char in value:
                font=ImageFont.truetype(latin if ord(char)<0x2e80 else chinese,size)
                draw.text((px,y+size),char,font=font,fill=color,anchor='ls');px+=draw.textlength(char,font=font)
    def arrow(x1,y1,x2,y2,color='#839dbb'):
        if x1==x2: points=[(x2-7,y2-10),(x2+7,y2-10),(x2,y2)];end=(x2,y2-9)
        else: points=[(x2+10,y2-7),(x2+10,y2+7),(x2,y2)];end=(x2+9,y2)
        svg.append(f'<path d="M {x1} {y1} L {end[0]} {end[1]}" stroke="{color}" stroke-width="3"/><polygon points="'+ ' '.join(f'{x},{y}' for x,y in points)+f'" fill="{color}"/>')
        if draw: draw.line((x1,y1,*end),fill=color,width=3);draw.polygon(points,fill=color)
    text(60,28,'通用知识初始化 · 文档功能发现 → 源码扩展发现',34)
    text(60,83,'三个大阶段 + 一个目录发现交接步骤；适用于服务、SDK、前端与多语言仓库',20,'#62738a')
    rect(60,135,1070,85,'#e7f2ff','#bad5f4')
    text(80,147,'选择仓库 → 加载适配配置 → 固定源码 SHA 与本轮范围',25,'#20568b')
    text(80,184,'已有目录作为种子；旧仓库显式启用发现，新初始化配置启用目录发现。',18,'#62738a')
    for n,(a,b) in enumerate([('源码与测试','生产库存、入口、导出与断言'),('项目文档','README、架构、API 与指南'),('维护者资料','局部知识与设计决策'),('已有知识','稳定功能 ID 与 owner 路由')]):
        x=60+n*270;rect(x,250,250,62,'#ffffff','#dce4ee');text(x+12,258,a,20,'#20568b');text(x+12,286,b,13,'#62738a')
    rect(60,345,1070,125,'#ffffff','#c9d9ec')
    text(80,357,'阶段 1 · Skeleton：建骨架',26,'#20568b')
    text(80,399,'确定仓库、目录与初始组件边界，明确后续扫描范围与索引策略。',20)
    text(80,434,'范围和排除规则由仓库配置确定；未知语言保留文本发现与未解析记录。',18,'#62738a')
    arrow(595,470,595,535)
    rect(60,535,1070,460,'#f4efff','#d6c7ef')
    text(80,546,'阶段交接 · Feature Discovery：发现并冻结功能目录',26,'#704c9a')
    rows=[('文档轮：建立功能基线','建立共享索引，按文件识别语言；提取文档正文中的能力与边界。'),
          ('源码轮：寻找更多功能','优先探索未关联入口，再遍历声明范围；CLI / API / UI / SDK / 注册 / 测试。'),
          ('聚合去重与独立评审','判断新增、实现补充、别名、子能力、共享组件、过期或未知；最多修正 3 次。'),
          ('目录 PR → 审查合并 → 冻结','保留旧 ID；实现证据与独立评审支持的新功能入列；绑定目录哈希与源码 SHA。')]
    for n,(a,b) in enumerate(rows):
        y=602+n*90;rect(80,y,1030,72,'#ffffff');text(97,y+7,a,22,'#704c9a');text(97,y+40,b,17,'#62738a')
        if n<3:arrow(595,y+72,595,y+90,'#a28bbc')
    text(80,971,'单项未知留在单项；预算耗尽或未处理分片保留检查点，不标为发现完成。',16,'#704c9a')
    arrow(595,995,595,1050)
    rect(60,1050,1070,135,'#ffffff','#c9d9ec')
    text(80,1062,'阶段 2 · Modules / Knowledge：铺广度',26,'#20568b')
    text(80,1105,'使用冻结功能目录建立组件导航、基础说明、源码关联与缺口清单。',20)
    text(80,1144,'新 owner 在本阶段建立；有源码但无文档的功能仍可提取，结构与深度分开统计。',17,'#62738a')
    arrow(595,1185,595,1240)
    rect(60,1240,1070,235,'#ffffff','#c9d9ec')
    text(80,1252,'阶段 3 · Deepen / Acceptance：做深度并验收',26,'#20568b')
    for n,line in enumerate(['按功能补齐七维知识 → Codex 独立评审 → 有限修正与未知留存',
                             '引用、哈希与认可记录审计 → 检索验收 → 独立审查 → CI → PR 交付',
                             '默认 GLM‑5.3 提取 / Codex 评审；共享并发 13，可通过批次配置覆盖',
                             '生产结构、知识认可、测试覆盖与真实 PR 效果分别报告；费用未报告则未知']):
        text(80,1297+n*37,line,18,'#62738a')
    rect(1170,135,370,275,'#eaf5ee','#bedcc9');text(1190,152,'贯穿流程的仓库配置',23,'#2a6b45')
    for n,line in enumerate(['源码 SHA、范围与文档入口','逐文件语言与测试框架','owner 边界、模型与运行预算','发现目录冻结后采用 N × 7 分母','','工具流程共用，知识按仓库隔离']):text(1190,200+n*30,line,18,'#345e46')
    cards=[(465,'输入与索引适配',['生产源码 / 测试 / 排除范围','未知语言不当作没有功能'],407),
           (665,'两轮发现共用输入',['文档建立基线，源码扩展','完整库存、分片与证据引用'],705),
           (1050,'组件与任务适配',['Agent：运行时 / 渠道 / 客户端','推理：引擎 / 模型 / 后端'],1117),
           (1300,'政策驱动验收',['采用本仓库覆盖目标与预算','核对冻结目录和真实注入内容'],1380)]
    for y,title,lines,target in cards:
        rect(1170,y,370,120,'#eaf5ee','#bedcc9');text(1190,y+13,title,22,'#2a6b45')
        for n,line in enumerate(lines):text(1190,y+54+n*30,line,17,'#345e46')
        # Explicit configuration flow into each stage; connect index from its
        # card with a short elbow so it does not pass through the main boxes.
        if target<y:
            svg.append(f'<path d="M 1170 {y+60} H 1150 V {target}" fill="none" stroke="#2a6b45" stroke-width="3"/>')
            if draw: draw.line((1170,y+60,1150,y+60,1150,target),fill='#2a6b45',width=3)
            arrow(1150,target,1130,target,'#2a6b45')
        else: arrow(1170,target,1130,target,'#2a6b45')
    rect(60,1530,1480,105,'#18273e')
    text(82,1544,'发现目录的完整性与知识覆盖是两件事：固定版本、真实证据、独立审查、未知不充数',23,'#ffffff')
    text(82,1587,'目录是已审查能力清单；声明范围已处理，不等于所有功能均已发现。未找到测试不声称无测试或已通过。',18,'#d5e1f2')
    target=output/'init-feature-discovery-workflow-cn'
    target.with_suffix('.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial, Droid Sans Fallback, sans-serif"><rect width="100%" height="100%" fill="#f3f6fb"/>'+''.join(svg)+'</svg>')
    if canvas: canvas.save(target.with_suffix('.png'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'eval/feature-discovery/visualizations')
    parser.add_argument('--png',action='store_true',help='also render PNG; requires Pillow and system CJK fonts')
    args=parser.parse_args();render(args.output,args.png)
