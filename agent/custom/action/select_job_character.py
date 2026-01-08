from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


@AgentServer.custom_action("select_job_character")
class SelectJobCharacter(CustomAction):
    """
    根据配置中的 job 参数，识别并点击对应的职业角色
    
    支持两种识别方式：
    1. TemplateMatch - 通过模板图片识别
    2. OCR - 通过文字识别
    
    配置示例（通过 pipeline_override）：
    {
        "SelectJobCharacter": {
            "job": "warrior",
            "use_template": true,  // 使用模板识别
            "template_path": "warrior.png"
        }
    }
    或
    {
        "RecognizeJobCharacter": {
            "job": "warrior",
            "use_ocr": true,  // 使用 OCR 识别
            "ocr_text": "战士"
        }
    }
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

    # 职业名称到模板图片路径的映射（用于 TemplateMatch）
    JOB_TEMPLATE_PATH = {
        "warrior": "warrior.png",      # TODO: 替换为真实模板路径
        "mage": "mage.png",
        "rogue": "rogue.png",
        "hunter": "hunter.png",
        "paladin": "paladin.png",
        "warlock": "warlock.png",
        "druid": "druid.png",
        "shaman": "shaman.png",
        "priest": "priest.png",
        "death_knight": "death_knight.png",
        "monk": "monk.png",
        "demon_hunter": "demon_hunter.png",
    }

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        job_name = None
        use_template = False
        use_ocr = False
        template_path = None
        ocr_text = None

        # 从 pipeline 配置中读取 job 参数和识别方式
        if hasattr(context, "config") and isinstance(context.config, dict):
            # 方式1: 从 SelectJobCharacter 节点配置读取
            select_config = context.config.get("SelectJobCharacter", {})
            if isinstance(select_config, dict):
                job_name = select_config.get("job")
                use_template = select_config.get("use_template", False)
                template_path = select_config.get("template_path")
                use_ocr = select_config.get("use_ocr", False)
                ocr_text = select_config.get("ocr_text")

            # 方式2: 从 RecognizeJobCharacter 节点配置读取
            if not job_name:
                recognize_config = context.config.get("RecognizeJobCharacter", {})
                if isinstance(recognize_config, dict):
                    job_name = recognize_config.get("job")
                    use_template = recognize_config.get("use_template", False)
                    template_path = recognize_config.get("template_path")
                    use_ocr = recognize_config.get("use_ocr", False)
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
            return False

        print(f"[SelectJobCharacter] Selecting job: {job_name}")

        # 确定识别方式：优先使用配置的，否则根据是否有模板路径决定
        if not use_template and not use_ocr:
            # 如果都没有指定，默认使用模板识别（如果有模板路径）
            if job_name in self.JOB_TEMPLATE_PATH:
                use_template = True
            else:
                # 否则使用 OCR
                use_ocr = True

        # 执行识别和点击
        if use_template:
            return self._select_by_template(context, job_name, template_path)
        elif use_ocr:
            return self._select_by_ocr(context, job_name, ocr_text)
        else:
            print(f"[SelectJobCharacter] Error: no recognition method specified")
            return False

    def _select_by_template(self, context: Context, job_name: str, template_path: str = None) -> bool:
        """通过模板匹配识别并点击角色"""
        if not template_path:
            template_path = self.JOB_TEMPLATE_PATH.get(job_name)
            if not template_path:
                print(f"[SelectJobCharacter] Error: no template path for job '{job_name}'")
                return False

        print(f"[SelectJobCharacter] Using template: {template_path}")

        try:
            # 获取当前截图
            image = context.tasker.controller.screencap()
            if not image:
                print(f"[SelectJobCharacter] Failed to capture screen")
                return False

            # 使用 TemplateMatch 识别
            # 注意：这里需要先配置好 TemplateMatch 的 pipeline 节点，或者使用 run_task
            # 更简单的方式是直接使用 pipeline 节点，而不是在 action 中调用 run_recognition
            # 但为了灵活性，我们尝试使用 run_recognition
            
            # 方法1: 使用 run_recognition（需要 pipeline 中有对应的识别节点）
            try:
                reco_detail = context.run_recognition(
                    "TemplateMatch",
                    image,
                    pipeline_override={
                        "TemplateMatch": {
                            "template": template_path,
                            "threshold": 0.8,
                        }
                    }
                )

                if reco_detail and hasattr(reco_detail, "box"):
                    # 获取识别到的位置并点击
                    box = reco_detail.box
                    center_x = (box[0] + box[2]) // 2
                    center_y = (box[1] + box[3]) // 2

                    print(f"[SelectJobCharacter] Found character at ({center_x}, {center_y})")
                    click_job = context.tasker.controller.post_click(center_x, center_y)
                    click_job.wait()
                    return True
                else:
                    print(f"[SelectJobCharacter] Template not found: {template_path}")
                    return False
            except Exception as e:
                print(f"[SelectJobCharacter] run_recognition failed, trying alternative method: {e}")
                # 如果 run_recognition 失败，可以尝试其他方法
                # 例如：直接运行一个包含 TemplateMatch 的 pipeline 节点
                return False

        except Exception as e:
            print(f"[SelectJobCharacter] Template recognition failed: {e}")
            return False

    def _select_by_ocr(self, context: Context, job_name: str, ocr_text: str = None) -> bool:
        """通过 OCR 识别并点击角色"""
        if not ocr_text:
            ocr_text = self.JOB_OCR_TEXT.get(job_name)
            if not ocr_text:
                print(f"[SelectJobCharacter] Error: no OCR text for job '{job_name}'")
                return False

        print(f"[SelectJobCharacter] Using OCR text: {ocr_text}")

        try:
            # 获取当前截图
            image = context.tasker.controller.screencap()
            if not image:
                print(f"[SelectJobCharacter] Failed to capture screen")
                return False

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
                    click_job = context.tasker.controller.post_click(center_x, center_y)
                    click_job.wait()
                    return True
                else:
                    print(f"[SelectJobCharacter] OCR text not found: {ocr_text}")
                    return False
            except Exception as e:
                print(f"[SelectJobCharacter] run_recognition failed: {e}")
                return False

        except Exception as e:
            print(f"[SelectJobCharacter] OCR recognition failed: {e}")
            return False
