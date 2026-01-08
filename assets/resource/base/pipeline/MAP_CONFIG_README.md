# 地图配置说明

## 概述

本系统支持 8 个地图的自动清理，每个地图都有对应的入口函数和点击坐标配置。

## 地图入口函数

所有地图的入口函数定义在 `assets/resource/pipeline/map_cleanup.json` 中：

- `EastContinent` - 东方大陆
- `VoidRealm` - 虚空领域
- `FrozenContinent` - 冰封大陆
- `ElementalLand` - 元素之地
- `MistyContinent` - 迷雾大陆
- `ShadowContinent` - 暗影大陆
- `LegionDomain` - 军团领域
- `StormIsles` - 风暴群岛

每个入口都调用 `map_cleanup` action，该 action 会：
1. 读取 interface.json 中配置的职业开关（use_warrior, use_mage 等）
2. 遍历所有开启的职业
3. 对每个职业调用 `MapJobCommon` pipeline
4. `MapJobCommon` 会调用 `FreeDungeonTask` 执行实际的刷图流程

## 地图点击坐标配置

### 方式 1：在代码中配置（推荐用于默认值）

在 `agent/custom/action/map_cleanup.py` 中的 `MAP_CLICK_COORDINATES` 字典配置：

```python
MAP_CLICK_COORDINATES = {
    "EastContinent": [100, 200],      # [x, y] 坐标
    "VoidRealm": [200, 200],
    # ... 其他地图
}
```

### 方式 2：通过 pipeline_override 覆盖（推荐用于个性化配置）

如果你想为某个地图使用不同的坐标，可以在 `agent/custom/action/map_cleanup.py` 中修改代码，让它从 `map_config` 中读取 `map_click_x` 和 `map_click_y`。

**注意**：当前代码已经支持从 pipeline_override 读取坐标覆盖。你可以在 interface.json 中为每个地图的 entry 添加配置，但需要修改代码来支持从顶层读取。

### 方式 3：直接在 select_map action 中配置

`agent/custom/action/select_map.py` 中的 `DEFAULT_MAP_COORDINATES` 也提供了后备坐标。

## 完整流程

1. 用户在 interface.json 中选择地图任务（例如"东方大陆"）
2. 系统调用对应的 entry（例如 `EastContinent`）
3. `map_cleanup.json` 中的 `EastContinent` 节点调用 `map_cleanup` action
4. `map_cleanup` action：
   - 读取该地图的职业开关配置
   - 获取地图点击坐标（从代码或 pipeline_override）
   - 遍历每个开启的职业，调用 `MapJobCommon`
5. `MapJobCommon` → `FreeDungeonTask` → `ClickMapEntry` → `ClickMapSelector` → `SelectMapByParam`
6. `SelectMapByParam` 使用 `select_map` action，根据配置的坐标点击对应地图

## 配置示例

### 在 interface.json 中配置职业开关

```json
{
    "task": [
        {
            "name": "东方大陆Lv.1-Lv.60",
            "entry": "EastContinent",
            "option": ["战士", "法师"]
        }
    ],
    "option": {
        "战士": {
            "type": "switch",
            "cases": [
                {
                    "name": "Yes",
                    "pipeline_override": {
                        "EastContinent": {
                            "use_warrior": true
                        }
                    }
                }
            ]
        }
    }
}
```

### 修改地图坐标

编辑 `agent/custom/action/map_cleanup.py`：

```python
MAP_CLICK_COORDINATES = {
    "EastContinent": [360, 200],  # 修改为你的真实坐标
    # ...
}
```

## 注意事项

1. 坐标格式为 `[x, y]`，单位是像素
2. 坐标是相对于游戏窗口的绝对坐标
3. 如果坐标配置错误，`select_map` action 会使用默认坐标或报错
4. 建议先用测试任务验证坐标是否正确
