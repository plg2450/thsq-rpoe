#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试小米MiMo TTS API集成
"""

import os
import sys
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MIMO_API_KEY, MIMO_BASE_URL, MIMO_TTS_MODEL


def test_api_connection():
    """测试API连接"""
    print("=" * 60)
    print("测试小米MiMo TTS API连接")
    print("=" * 60)

    import requests

    headers = {
        "Authorization": f"Bearer {MIMO_API_KEY}",
        "Content-Type": "application/json"
    }

    # 测试获取模型列表
    url = f"{MIMO_BASE_URL}/models"
    print(f"测试连接: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        print("[OK] API连接成功!")
        print(f"可用模型: {[m['id'] for m in result.get('data', [])]}")
        return True
    except Exception as e:
        print(f"[FAIL] API连接失败: {e}")
        return False


def test_tts_generation():
    """测试TTS语音生成（无语音克隆）"""
    print("\n" + "=" * 60)
    print("测试TTS语音生成（无语音克隆）")
    print("=" * 60)

    from core.voice_cloner import VoiceCloner

    cloner = VoiceCloner()
    test_text = "你好，这是一个测试。"

    # 创建临时输出文件
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        output_path = f.name

    try:
        print(f"测试文本: {test_text}")
        print(f"输出路径: {output_path}")

        result = cloner.generate_speech_from_text(test_text, output_path)
        print(f"[OK] TTS生成成功!")
        print(f"输出文件: {result}")

        # 检查文件是否存在和大小
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"文件大小: {file_size} bytes")
            if file_size > 0:
                print("[OK] 文件内容有效!")
            else:
                print("[FAIL] 文件为空!")
                return False
        else:
            print("[FAIL] 文件不存在!")
            return False

        return True

    except Exception as e:
        print(f"[FAIL] TTS生成失败: {e}")
        return False

    finally:
        # 清理临时文件
        if os.path.exists(output_path):
            os.remove(output_path)


def test_voice_clone():
    """测试语音克隆（需要参考音频）"""
    print("\n" + "=" * 60)
    print("测试语音克隆")
    print("=" * 60)

    from core.voice_cloner import VoiceCloner

    cloner = VoiceCloner()

    # 查找测试音频文件
    test_audio = None
    for ext in ["*.wav", "*.mp3", "*.flac"]:
        import glob
        files = glob.glob(os.path.join("data", "**", ext), recursive=True)
        if files:
            test_audio = files[0]
            break

    if not test_audio:
        print("[WARN] 未找到测试音频文件，跳过语音克隆测试")
        print("  请先录制或上传音频到 data/voice_profiles/ 目录")
        return True  # 返回True，不阻塞其他测试

    try:
        print(f"使用参考音频: {test_audio}")

        # 提取voice_id（实际上是DataURL）
        voice_info = cloner.extract_embedding(test_audio)
        voice_data_url = voice_info.get("voice_id")
        print(f"[OK] 成功提取语音特征")
        print(f"DataURL长度: {len(voice_data_url)} 字符")

        # 测试使用voice_id生成语音
        test_text = "这是用你的声音生成的测试语音。"
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        result = cloner.generate_speech_from_text(test_text, output_path, voice_data_url)
        print(f"[OK] 语音克隆生成成功!")
        print(f"输出文件: {result}")

        # 检查文件
        if os.path.exists(result):
            file_size = os.path.getsize(result)
            print(f"文件大小: {file_size} bytes")

        # 清理
        os.remove(output_path)

        return True

    except Exception as e:
        print(f"[FAIL] 语音克隆测试失败: {e}")
        return False


def test_save_load_embedding():
    """测试保存和加载voice信息"""
    print("\n" + "=" * 60)
    print("测试保存和加载voice信息")
    print("=" * 60)

    from core.voice_cloner import VoiceCloner

    cloner = VoiceCloner()

    # 创建测试数据
    test_voice_info = {
        "voice_id": "data:audio/wav;base64,test_data",
        "audio_path": "test.wav"
    }

    # 创建临时文件
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        save_path = f.name

    try:
        # 保存
        cloner.save_embedding(test_voice_info, save_path)
        print(f"[OK] 成功保存voice信息")

        # 加载
        loaded_info = cloner.load_embedding(save_path)
        print(f"[OK] 成功加载voice信息")

        # 验证
        if loaded_info.get("voice_id") == test_voice_info["voice_id"]:
            print("[OK] 数据验证通过!")
            return True
        else:
            print("[FAIL] 数据验证失败!")
            return False

    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        return False

    finally:
        # 清理
        if os.path.exists(save_path):
            os.remove(save_path)


def main():
    """主测试函数"""
    print("小米MiMo TTS API集成测试")
    print("=" * 60)

    results = []

    # 测试1: API连接
    results.append(("API连接", test_api_connection()))

    # 测试2: TTS生成（无克隆）
    results.append(("TTS生成", test_tts_generation()))

    # 测试3: 语音克隆
    results.append(("语音克隆", test_voice_clone()))

    # 测试4: 保存和加载
    results.append(("保存加载", test_save_load_embedding()))

    # 打印测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"{name}: {status}")

    all_passed = all(passed for _, passed in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("[OK] 所有测试通过!")
    else:
        print("[FAIL] 部分测试失败!")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
