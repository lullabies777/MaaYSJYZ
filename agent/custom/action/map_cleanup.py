from typing import Dict, List

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("MapCleanup")
class MapCleanup(CustomAction):
    """
    通用地图清理动作：
    - 当前地图通过任务名 / entry 名区分（例如 EastContinent、VoidRealm 等）
    - 职业开关来自 interface 中对该 entry 的 pipeline_override（use_xxx）
    - 在这里统一遍历所有勾选的职业并逐个执行清理逻辑
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        # 任务名就是 entry 名（例如 EastContinent / VoidRealm / ...）
        current_map = argv.node_name
        print("current_map:",current_map)
        node_obj = context.get_node_object(current_map)
        attach = getattr(node_obj, "attach", {}) if node_obj else {}

        # 收集所有已开启的职业
        enabled_jobs = self._collect_enabled_jobs(attach)
        print("enabled_jobs:", enabled_jobs)

        print(f"[MapCleanup] map={current_map}, jobs={enabled_jobs}")

        # 逐个职业执行清理
        for job in enabled_jobs:
            result = self._run_one_job(context, current_map, job)
            if not getattr(result, "success", False):
                print(f"[MapCleanup] job {job} failed on {current_map}")
                return result

        return CustomAction.RunResult(success=True)

    @staticmethod
    def _collect_enabled_jobs(attach):
        """
        根据 use_xxx 布尔字段收集需要执行的职业。
        这些字段来自 interface.json 的 pipeline_override。
        """
        job_keys = {
            "use_warrior": "warrior",
            "use_mage": "mage",
            "use_rogue": "rogue",
            "use_hunter": "hunter",
            "use_paladin": "paladin",
            "use_warlock": "warlock",
            "use_druid": "druid",
            "use_shaman": "shaman",
            "use_priest": "priest",
            "use_death_knight": "death_knight",
            "use_monk": "monk",
            "use_demon_hunter": "demon_hunter",
        }
        enabled = []
        for key, name in job_keys.items():
            if attach.get(key, False):
                enabled.append(name)
        return enabled

    def _run_one_job(self, context: Context, map_name: str, job_name: str) -> CustomAction.RunResult:
        """
        单个职业的执行逻辑：
        - 通过 pipeline_override 将 map / job 信息写入通用子流水线 MapJobCommon
        - 然后调用该子流水线，让复杂流程都在 pipeline 里实现
        """
        print(f"[MapCleanup] dispatch job={job_name} on map={map_name} -> MapJobCommon")

        # 将当前 map / job 信息和地图坐标写入通用子流水线配置（V2 范式）
        # 使用 action.param.custom_action_param 格式传递参数
        context.override_pipeline(
            {
                "RecognizeJobCharacter": {
                    "action": {
                        "type": "Custom",
                        "param": {
                            "custom_action": "SelectJob",
                            "custom_action_param": {
                                "job": job_name
                            }
                        }
                    }
                },
                "SelectMapByParam": {
                    "action": {
                        "type": "Custom",
                        "param": {
                            "custom_action": "SelectMap",
                            "custom_action_param": {
                                "map": map_name
                            }
                        }
                    }
                }
            }
        )

        # 运行通用子流水线，由它内部决定如何 OCR / 点击 / 刷图
        try:
            context.run_task("MapJobCommon")
        except Exception as e:
            print(f"[MapCleanup] MapJobCommon failed for {map_name}/{job_name}: {e}")
            return CustomAction.RunResult(success=False)

        return CustomAction.RunResult(success=True)
