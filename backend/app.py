"""OS 调试助手的 Flask Web 服务器"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# 将当前目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzers.hypothesis_engine import HypothesisEngine

# 创建 Flask 应用实例
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # 启用 CORS 支持，用于开发环境的跨域请求

# 初始化假设引擎（核心分析引擎）
engine = HypothesisEngine()


@app.route('/')
def index():
    """
    提供主页 HTML 文件

    返回:
        前端页面 index.html
    """
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    主要分析 API 端点

    接收 JSON 格式: {"text": "...调试输出..."}
    返回 JSON 格式的分析结果，包括:
        - success: 是否成功
        - summary: 分析摘要
        - hypotheses: 假设列表
        - gdb_analysis: GDB 分析结果
        - trapframe_analysis: 陷阱帧分析结果
        - pagetable_analysis: 页表分析结果
        - all_findings: 所有发现的问题
    """
    try:
        # 获取 JSON 数据
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': '请求中缺少 "text" 字段'}), 400

        text = data['text']
        if not text or not text.strip():
            return jsonify({'error': '输入文本为空'}), 400

        # 运行分析引擎
        result = engine.analyze(text)

        # 格式化响应数据
        response = {
            'success': True,
            'summary': result.get('summary', ''),
            'hypotheses': result.get('hypotheses', []),
            'gdb_analysis': result.get('gdb_analysis'),
            'trapframe_analysis': result.get('trapframe_analysis'),
            'pagetable_analysis': result.get('pagetable_analysis'),
            'all_findings': result.get('all_findings', [])
        }

        return jsonify(response)

    except Exception as e:
        # 捕获并返回错误信息
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """
    健康检查端点

    用于检测服务是否正常运行

    返回:
        JSON: {'status': 'ok'}
    """
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    # 从环境变量获取配置，提供默认值
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    print(f"正在启动 OS 调试助手，端口: {port}")
    print(f"调试模式: {debug}")
    print(f"访问地址: http://localhost:{port}")

    # 启动 Flask 应用
    # host='0.0.0.0' 允许外部访问
    app.run(host='0.0.0.0', port=port, debug=debug)
