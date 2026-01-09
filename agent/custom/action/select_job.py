from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
import json


@AgentServer.custom_action("SelectJob")
class SelectJob(CustomAction):
    """
    根据 custom_action_param 中的 job 参数，仅通过 OCR 识别并点击对应职业角色。
    
    参数格式（通过 custom_action_param）：
    {
        "job": "warrior",
        "ocr_text": "战士",  // 可选，如果不提供则使用内置映射
        "offset_x": 0,       // 可选，点击位置相对识别框中心的 x 偏移
        "offset_y": -40      // 可选，点击位置相对识别框中心的 y 偏移（负数表示向上）
    }
    """
    def __init__(self):
        super().__init__()
        # 职业名称到识别文本的映射（用于 OCR）
        self.JOB_OCR_TEXT = {
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
        self.JOB_COORD = {
            "warrior": [0,0],
            "mage": [0,0],
            "rogue": [0,0],
            "hunter": [0,0],
            "paladin": [0,0],
            "warlock": [0,0],
            "druid": [0,0],
            "shaman": [0,0],
            "priest": [0,0],
            "death_knight": [0,0],
            "monk": [0,0],
            "demon_hunter": [0,0],
        }

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        job_name = None
        ocr_text = None
        # offset_x = 0
        # offset_y = -40  # 默认向上偏移 40 像素

        # 从 custom_action_param 读取参数（V2 范式）
        try:
            if argv.custom_action_param:
                custom_action_param = json.loads(argv.custom_action_param)
                job_name = custom_action_param.get("job")
        except Exception as e:
            print(f"[SelectJobCharacter] Error parsing custom_action_param: {e}")

        if not job_name:
            print(f"[SelectJobCharacter] Error: job parameter not found")
            return CustomAction.RunResult(success=False)

        print(f"[SelectJobCharacter] Selecting job by OCR: {job_name}")

        return self._select_by_coord(context, job_name)

    def _select_by_coord(self, context, job_name):
        
        click_x, click_y = self.JOB_COORD[job_name]
        click_job = context.tasker.controller.post_click(click_x, click_y)
        click_job.wait()
        return CustomAction.RunResult(success=True)
        
    # def _select_by_ocr(self, context: Context, job_name: str, offset_x: int = 0, offset_y: int = -40) -> CustomAction.RunResult:
    #     """通过 OCR 识别并点击角色"""

    #     ocr_text = self.JOB_OCR_TEXT.get(job_name)
    #     if not ocr_text:
    #         print(f"[SelectJobCharacter] Error: no OCR text for job '{job_name}'")
    #         return CustomAction.RunResult(success=False)

    #     print(f"[SelectJobCharacter] Using OCR text: {ocr_text}")

    #     try:
    #         # 获取当前截图
    #         image = context.tasker.controller.post_screencap().wait().get()
           
    #         # 使用 OCR 识别
    #         try:
    #             reco_detail = context.run_recognition(
    #                 "OCRJob",
    #                 image
    #             )
    #             print("reco_detail",reco_detail)
    #             if reco_detail and hasattr(reco_detail, "box"):
    #                 # 获取识别到的位置并应用偏移
    #                 box = reco_detail.box
    #                 center_x = (box[0] + box[2]) // 2
    #                 center_y = (box[1] + box[3]) // 2

    #                 # 应用偏移量
    #                 click_x = center_x + offset_x
    #                 click_y = center_y + offset_y

    #                 print(f"[SelectJobCharacter] Found character text at ({center_x}, {center_y}), clicking at ({click_x}, {click_y})")

    #                 click_job = context.tasker.controller.post_click(click_x, click_y)
    #                 click_job.wait()
    #                 return CustomAction.RunResult(success=True)
    #             else:
    #                 print(f"[SelectJobCharacter] OCR text not found: {ocr_text}")
    #                 return CustomAction.RunResult(success=False)
    #         except Exception as e:
    #             print(f"[SelectJobCharacter] run_recognition failed: {e}")
    #             return CustomAction.RunResult(success=False)

    #     except Exception as e:
    #         print(f"[SelectJobCharacter] OCR recognition failed: {e}")
    #         return CustomAction.RunResult(success=False)
