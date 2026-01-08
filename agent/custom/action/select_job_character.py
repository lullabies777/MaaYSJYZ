from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("select_job_character")
class SelectJobCharacter(CustomAction):
    """
    根据配置中的 job 参数，仅通过 OCR 识别并点击对应职业角色。

    配置来源优先级：
    1. pipeline_override 中的 SelectJobCharacter / RecognizeJobCharacter 节点
    2. MapJobCommon / FreeDungeonTask 中的 job 字段（由 map_cleanup 写入）

    OCR 文本优先使用节点里的 ocr_text，若未设置，则使用内置映射 JOB_OCR_TEXT。
    """

    # 职业名称到识别文本的映射（用于 OCR）
    JOB_OCR_TEXT = {
        "warrior": "战士",
        "mage": "法师",
        "rogue": "盗贼",
        "hunter": "猎人",
        "paladin": "圣骑士",
        "warlock": "术士",
        "druid": "德鲁伊",
        "shaman": "萨满祭祀",
        "priest": "牧师",
        "death_knight": "死亡骑士",
        "monk": "武僧",
        "demon_hunter": "魔猎手",
    }

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        job_name = None
        ocr_text = None

        # 从 pipeline 配置中读取 job 参数和识别方式
        if hasattr(context, "config") and isinstance(context.config, dict):
            # 方式1: 从 SelectJobCharacter 节点配置读取
            select_config = context.config.get("SelectJobCharacter", {})
            if isinstance(select_config, dict):
                job_name = select_config.get("job")
                ocr_text = select_config.get("ocr_text")

            # 方式2: 从 RecognizeJobCharacter 节点配置读取
            if not job_name:
                recognize_config = context.config.get("RecognizeJobCharacter", {})
                if isinstance(recognize_config, dict):
                    job_name = recognize_config.get("job")
                    ocr_text = recognize_config.get("ocr_text")

            # 方式3: 从 MapJobCommon 或 FreeDungeonTask 配置读取
            if not job_name:
                for key in ["MapJobCommon", "FreeDungeonTask"]:
                    task_config = context.config.get(key, {})
                    if isinstance(task_config, dict):
                        job_name = task_config.get("job")
                        if job_name:
                            break

        if not job_name:
            print(f"[SelectJobCharacter] Error: job parameter not found")
            return CustomAction.RunResult(success=False)

        print(f"[SelectJobCharacter] Selecting job by OCR: {job_name}")

        return self._select_by_ocr(context, job_name, ocr_text)

    def _select_by_ocr(self, context: Context, job_name: str, ocr_text: str = None) -> CustomAction.RunResult:
        """通过 OCR 识别并点击角色"""
        if not ocr_text:
            ocr_text = self.JOB_OCR_TEXT.get(job_name)
            if not ocr_text:
                print(f"[SelectJobCharacter] Error: no OCR text for job '{job_name}'")
                return CustomAction.RunResult(success=False)

        print(f"[SelectJobCharacter] Using OCR text: {ocr_text}")

        try:
            # 获取当前截图
            image = context.tasker.controller.screencap()
            if not image:
                print(f"[SelectJobCharacter] Failed to capture screen")
                return CustomAction.RunResult(success=False)

            # 使用 OCR 识别
            try:
                reco_detail = context.run_recognition(
                    "OCR",
                    image,
                    pipeline_override={
                        "OCR": {
                            "text": ocr_text,
                        }
                    }
                )

                if reco_detail and hasattr(reco_detail, "box"):
                    # 获取识别到的位置并点击
                    box = reco_detail.box
                    center_x = (box[0] + box[2]) // 2
                    center_y = (box[1] + box[3]) // 2

                    print(f"[SelectJobCharacter] Found character text at ({center_x}, {center_y})")
                    
                    # add offset to the center of the character
                    click_x = center_x
                    click_y = center_y - 40

                    click_job = context.tasker.controller.post_click(center_x, center_y)
                    click_job.wait()
                    return CustomAction.RunResult(success=True)
                else:
                    print(f"[SelectJobCharacter] OCR text not found: {ocr_text}")
                    return CustomAction.RunResult(success=False)
            except Exception as e:
                print(f"[SelectJobCharacter] run_recognition failed: {e}")
                return CustomAction.RunResult(success=False)

        except Exception as e:
            print(f"[SelectJobCharacter] OCR recognition failed: {e}")
            return CustomAction.RunResult(success=False)
