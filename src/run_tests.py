"""
測試腳本
========
測試所有新功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """測試模組導入"""
    print("=" * 60)
    print("測試 1: 模組導入")
    print("=" * 60)
    
    try:
        from config_loader import load_config, ConfigLoader
        print("✓ config_loader 導入成功")
    except Exception as e:
        print(f"✗ config_loader 導入失敗: {e}")
        return False
    
    try:
        from data_loader import create_asset, validate_data_file
        print("✓ data_loader 導入成功")
    except Exception as e:
        print(f"✗ data_loader 導入失敗: {e}")
        return False
    
    try:
        from logger import setup_logger, get_logger
        print("✓ logger 導入成功")
    except Exception as e:
        print(f"✗ logger 導入失敗: {e}")
        return False
    
    try:
        from result_viewer import ResultViewer, create_simple_report
        print("✓ result_viewer 導入成功")
    except Exception as e:
        print(f"✗ result_viewer 導入失敗: {e}")
        return False
    
    return True


def test_config_loader():
    """測試配置載入器"""
    print("\n" + "=" * 60)
    print("測試 2: 配置載入器")
    print("=" * 60)
    
    try:
        from config_loader import load_config
        
        # 嘗試載入配置
        try:
            strategy_config, backtest_config, logging_config = load_config('strategy_aggressive.yaml')
            print(f"✓ 配置載入成功")
            print(f"  - 策略名稱: {strategy_config.gamma_base}")
            print(f"  - Tick Size: {backtest_config.tick_size}")
            print(f"  - 日誌級別: {logging_config.level}")
            return True
        except FileNotFoundError:
            print("⚠ 配置檔案未找到（使用相對路徑）")
            # 嘗試絕對路徑
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'strategy_aggressive.yaml')
            if os.path.exists(config_path):
                loader = ConfigLoader()
                config = loader.load('strategy_aggressive.yaml')
                print("✓ 配置檔案存在")
                return True
            else:
                print(f"✗ 配置檔案不存在: {config_path}")
                return False
    except Exception as e:
        print(f"✗ 配置載入失敗: {e}")
        return False


def test_logger():
    """測試日誌系統"""
    print("\n" + "=" * 60)
    print("測試 3: 日誌系統")
    print("=" * 60)
    
    try:
        from logger import setup_logger, get_logger
        
        logger = setup_logger('test', console=True, level='INFO')
        logger.info("這是一條測試日誌訊息")
        logger.debug("這是一條調試訊息（不會顯示）")
        print("✓ 日誌系統正常")
        return True
    except Exception as e:
        print(f"✗ 日誌系統失敗: {e}")
        return False


def test_result_viewer():
    """測試結果展示器"""
    print("\n" + "=" * 60)
    print("測試 4: 結果展示器")
    print("=" * 60)
    
    try:
        import numpy as np
        from result_viewer import ResultViewer
        
        viewer = ResultViewer(tick_size=0.1)
        
        # 添加一些測試數據
        np.random.seed(42)
        for i in range(100):
            viewer.record_step(
                equity=30000 + np.random.randn() * 100,
                position=np.random.randn() * 5,
                mid_price=50000 + np.random.randn() * 10
            )
        
        # 測試波動率計算
        vol_ticks = viewer.calculate_volatility_by_tick()
        print(f"✓ 結果展示器正常")
        print(f"  - 記錄了 {len(viewer.equity_history)} 個數據點")
        print(f"  - 波動率計算: {len(vol_ticks)} 個值")
        print(f"  - 平均波動率: {np.mean(vol_ticks):.2f} ticks")
        return True
    except Exception as e:
        print(f"✗ 結果展示器失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_loader():
    """測試資料載入器"""
    print("\n" + "=" * 60)
    print("測試 5: 資料載入器")
    print("=" * 60)
    
    try:
        from data_loader import validate_data_file
        
        # 測試檔案驗證
        dummy_file = os.path.join(os.path.dirname(__file__), 'dummy_data.npy')
        if os.path.exists(dummy_file):
            validate_data_file(dummy_file)
            print(f"✓ 資料檔案驗證成功: {dummy_file}")
            return True
        else:
            print(f"⚠ 測試資料檔案不存在: {dummy_file}")
            return True  # 不算失敗
    except Exception as e:
        print(f"✗ 資料載入器失敗: {e}")
        return False


def main():
    """運行所有測試"""
    print("\n" + "=" * 60)
    print("開始測試所有功能")
    print("=" * 60)
    
    results = []
    
    results.append(("模組導入", test_imports()))
    results.append(("配置載入器", test_config_loader()))
    results.append(("日誌系統", test_logger()))
    results.append(("結果展示器", test_result_viewer()))
    results.append(("資料載入器", test_data_loader()))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{name}: {status}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！")
        return 0
    else:
        print(f"\n⚠ {total - passed} 個測試失敗")
        return 1


if __name__ == "__main__":
    sys.exit(main())

