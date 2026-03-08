import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# إعداد السجلات (Logging) في ملف
logging.basicConfig(
    filename='inference.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

app = Flask(__name__)
CORS(app)

# --- الكيانات الأساسية للنظام الخبير ---

class Rule:
    def __init__(self, conditions, conclusion, explanation):
        self.conditions = conditions  # {fact: value}
        self.conclusion = conclusion  # {fact: value}
        self.explanation = explanation

    def is_triggered(self, working_memory):
        for fact, value in self.conditions.items():
            if working_memory.get(fact) != value:
                return False
        return True

class ExpertSystem:
    def __init__(self):
        self.knowledge_base = []
        self._initialize_rules()

    def _initialize_rules(self):
        """قاعدة معرفة متطورة: المرحلة 3 تعتمد على 3 أسئلة لكل مادة تخصص، مع ضمان الوصول لنهاية في كل مسار."""
        
        # --- المرحلة 1: التصنيف ---
        self.knowledge_base.append(Rule({"grade": "1st_secondary"}, {"category_ready": True}, "تم تحديد فئة الأول ثانوي."))
        self.knowledge_base.append(Rule({"grade": "3rd_secondary", "path": "أكاديمي"}, {"category_ready": True}, "تم تحديد المسار الأكاديمي لثالث ثانوي."))
        self.knowledge_base.append(Rule({"grade": "3rd_secondary", "path": "فني"}, {"category_ready": True}, "تم تحديد المسار الفني لثالث ثانوي."))

        # --- المرحلة 2: الميول (Meyul) ---
        # ميول أكاديمية
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_medicine": True}, {"meyul": "أحياء/طب"}, "تم اكتشاف ميول طبية."))
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_engineering": True}, {"meyul": "هندسة"}, "تم اكتشاف ميول هندسية."))
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_it": True}, {"meyul": "علوم حاسوب"}, "تم اكتشاف ميول برمجية."))
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_arts": True}, {"meyul": "فنون وتصميم"}, "تم اكتشاف ميول فنية."))
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_humanities": True}, {"meyul": "حقوق/إنسانيات"}, "تم اكتشاف ميول إنسانية وقانونية."))

        # ميول فنية
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_industrial": True}, {"meyul": "فني صناعي"}, "تم اكتشاف ميول صناعية."))
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_commercial": True}, {"meyul": "فني تجاري"}, "تم اكتشاف ميول تجارية."))
        self.knowledge_base.append(Rule({"category_ready": True, "prefers_agricultural": True}, {"meyul": "فني زراعي"}, "تم اكتشاف ميول زراعية."))
        self.knowledge_base.append(Rule({"category_ready": True, "gender": "female", "prefers_feminine": True}, {"meyul": "فني نسوي"}, "تم اكتشاف ميول لتصميم الأزياء."))

        # --- المرحلة 3: التحقق الفعلي (3 أسئلة لكل مادة تخصص) ---
        
        # 🧪 تخصص: أحياء / طب (المادة: العلوم الطبيعية)
        # الحالة 1: نجاح باهر (3 نعم)
        self.knowledge_base.append(Rule({"meyul": "أحياء/طب", "sci_q1": True, "sci_q2": True, "sci_q3": True}, 
            {"final_recommendation": "أحياء / طب", "advice": "تطابق تام! شغفك ودرجاتك في العلوم الطبيعية يؤكدان تميزك في المسار الطبي."}, "تأكيد المسار الطبي بنجاح كامل."))
        # الحالة 2: نجاح جزئي أو فشل (أي إجابة بـ لا في أي من الـ 3 أسئلة نعتبره "عدم كفاية تحصيل")
        # لتبسيط المنطق وضمان النهاية، سنستخدم شرط وجود الـ 3 إجابات مع وجود "لا" واحدة على الأقل
        # سنضيف قاعدة "جامعة" لكل المسارات الأخرى
        
        # 🏗 تخصص: هندسة (المواد: الرياضيات + تربية تقنية)
        self.knowledge_base.append(Rule({"meyul": "هندسة", "eng_q1": True, "eng_q2": True, "eng_q3": True}, 
            {"final_recommendation": "هندسة", "advice": "عبقري! تميزك في الرياضيات والتربية التقنية بالمتوسطة هو جواز سفرك للهندسة."}, "تأكيد المسار الهندسي."))
        
        # 💻 تخصص: علوم حاسوب (المادة: تكنولوجيا المعلومات)
        self.knowledge_base.append(Rule({"meyul": "علوم حاسوب", "it_q1": True, "it_q2": True, "it_q3": True}, 
            {"final_recommendation": "علوم حاسوب", "advice": "تطابق رقمي! مهاراتك في الـ IT وتركيزك بالمتوسطة يمهدان لك طريق البرمجة."}, "تأكيد مسار الحاسوب."))

        # 🎨 تخصص: فنون وتصميم (المادة: التربية الفنية)
        self.knowledge_base.append(Rule({"meyul": "فنون وتصميم", "art_q1": True, "art_q2": True, "art_q3": True}, 
            {"final_recommendation": "فنون وتصميم", "advice": "فنان مبدع! درجتك وميولك في التربية الفنية تؤهلانك لتكون مصمماً عالمياً."}, "تأكيد مسار الفنون."))

        # ⚖ تخصص: حقوق/إنسانيات (المادة: تاريخ / جغرافيا)
        self.knowledge_base.append(Rule({"meyul": "حقوق/إنسانيات", "hum_q1": True, "hum_q2": True, "hum_q3": True}, 
            {"final_recommendation": "حقوق / علوم إنسانية", "advice": "ثقافة قانونية! تفوقك في المواد الاجتماعية بالمتوسطة يدعم نجاحك كحقوقي أو باحث إنساني."}, "تأكيد مسار الإنسانيات."))

        # 🛠 المسارات الفنية (صناعي، تجاري، زراعي، نسوي)
        self.knowledge_base.append(Rule({"meyul": "فني صناعي", "ind_q1": True, "ind_q2": True, "ind_q3": True}, 
            {"final_recommendation": "فني صناعي", "advice": "فني محترف! مهاراتك التقنية العالية تجعل من تخصص الصناعة اختيارك الأول."}, "تأكيد المسار الصناعي."))
        
        self.knowledge_base.append(Rule({"meyul": "فني تجاري", "com_q1": True, "com_q2": True, "com_q3": True}, 
            {"final_recommendation": "فني تجاري", "advice": "منظم وحاسب! دقتك في المتوسطة ستجعل منك إدارياً أو محاسباً ناجحاً في المسار التجاري."}, "تأكيد المسار التجاري."))

        self.knowledge_base.append(Rule({"meyul": "فني زراعي", "agr_q1": True, "agr_q2": True, "agr_q3": True}, 
            {"final_recommendation": "فني زراعي متطور", "advice": "صديق البيئة! شغفك بالعلوم والبيئة بالمتوسطة يزهر في المسار الزراعي الحديث."}, "تأكيد المسار الزراعي."))

        self.knowledge_base.append(Rule({"meyul": "فني نسوي", "fem_q1": True, "fem_q2": True, "fem_q3": True}, 
            {"final_recommendation": "فني تصميم أزياء", "advice": "ذوق رفيع! مهاراتك الفنية واليدوية ستجعلك رائدة في عالم الأزياء."}, "تأكيد المسار النسوي."))

        # --- قواعد "الاستشارة البديلة" (عندما لا تكون الإجابات كلها "نعم") ---
        # سنستخدم قاعدة عامة: إذا تم إكمال الـ 3 أسئلة ولم تتحقق قاعدة "النجاح التام"، نوجه لاستشارة تغيير المسار أو تعديله.
        
        # البدائل (أمثلة لضمان استجابة كل المسارات)
        self.knowledge_base.append(Rule({"sci_q_done": True, "final_recommendation": None}, {"final_recommendation": "فني زراعي متطور", "advice": "استشارة: شغفك طبي ولكن تحصيلك العملي بالعلوم لم يكن كافياً؛ المسار الزراعي الحديث بوابة قريبة من اهتماماتك العلمية."}, "استشارة بديلة للطب."))
        self.knowledge_base.append(Rule({"eng_q_done": True, "final_recommendation": None}, {"final_recommendation": "فني صناعي", "advice": "استشارة: ميولك هندسية لكن درجاتك الرياضية تحتاج دعماً؛ المسار الفني الصناعي سيمنحك الخبرة العملية المطلوبة."}, "استشارة بديلة للهندسة."))
        self.knowledge_base.append(Rule({"it_q_done": True, "final_recommendation": None}, {"final_recommendation": "صيانة أجهزة ذكية", "advice": "استشارة: تحصيلك في البرمجة النظرية ضعيف؛ ننصحك بمسار فني متخصص في صيانة التقنيات الحديثة."}, "استشارة بديلة للحاسوب."))
        self.knowledge_base.append(Rule({"gen_q_done": True, "final_recommendation": None}, {"final_recommendation": "تطوير مهارات عامة", "advice": "استشارة: نوصي بالتركيز على المواد الأساسية وتقوية نقاط الضعف قبل اختيار تخصص دقيق."}, "نهاية عامة عند عدم التطابق."))

    def run_inference(self, facts):
        working_memory = facts.copy()
        working_memory["final_recommendation"] = None
        applied_rules = []
        
        # تحديد ما إذا كان تم إنهاء أسئلة المادة (التحقق من علم التحصيل)
        # سنقوم بتوليد facts صناعية تدل على "اكتمال الأسئلة" لتسهيل القواعد البديلة
        subjects_map = {
            "sci": ["sci_q1", "sci_q2", "sci_q3"],
            "eng": ["eng_q1", "eng_q2", "eng_q3"],
            "it": ["it_q1", "it_q2", "it_q3"],
            "art": ["art_q1", "art_q2", "art_q3"],
            "hum": ["hum_q1", "hum_q2", "hum_q3"],
            "ind": ["ind_q1", "ind_q2", "ind_q3"],
            "com": ["com_q1", "com_q2", "com_q3"],
            "agr": ["agr_q1", "agr_q2", "agr_q3"],
            "fem": ["fem_q1", "fem_q2", "fem_q3"]
        }
        for sub, keys in subjects_map.items():
            if all(k in working_memory for k in keys):
                working_memory[f"{sub}_q_done"] = True
                working_memory["gen_q_done"] = True

        logging.info(f"Processing facts: {working_memory}")
        
        changed = True
        while changed:
            changed = False
            for rule in self.knowledge_base:
                if rule.is_triggered(working_memory):
                    is_new = False
                    for k, v in rule.conclusion.items():
                        if working_memory.get(k) != v:
                            is_new = True
                            break
                    if is_new:
                        working_memory.update(rule.conclusion)
                        logging.info(f"Rule triggered: {rule.explanation} -> Result: {rule.conclusion}")
                        if rule.explanation not in applied_rules:
                            applied_rules.append(rule.explanation)
                        changed = True
        
        if working_memory.get("final_recommendation"):
            logging.info(f"Final Outcome: {working_memory['final_recommendation']}")
            return {
                "status": "final",
                "recommendation": working_memory["final_recommendation"],
                "advice": working_memory.get("advice", "بالتوفيق في مسارك المختار!"),
                "explanations": applied_rules
            }
        
        next_step = self._get_next_question(working_memory)
        logging.info(f"Next step prompted: {next_step.get('fact')}")
        next_step["explanations"] = applied_rules
        return next_step

    def _get_next_question(self, wm):
        # المرحلة 1: التصنيف
        if "gender" not in wm: return self._create_question("gender", "الجنس؟", "choice")
        if "grade" not in wm: return self._create_question("grade", "في أي مرحلة دراسية أنت الآن؟", "choice")
        
        grade = wm.get("grade")
        if grade == "3rd_secondary" and "path" not in wm:
            return self._create_question("path", "بما أنك في ثالث ثانوي، أي مسار تتبع حالياً؟", "choice")

        # المرحلة 2: الميول (تحديد الـ Path لطلاب أولى ثانوي)
        if "path" not in wm:
            if "prefers_academic" not in wm: return self._create_question("prefers_academic", "هل تميل للدراسة الأكاديمية والبحث العلمي؟")
            wm["path"] = "أكاديمي" if wm["prefers_academic"] else "فني"

        path = wm.get("path")
        if path == "أكاديمي":
            if "prefers_medicine" not in wm: return self._create_question("prefers_medicine", "هل تهتم بعلاج الناس واكتشاف أسرار الجسم البشري؟")
            if "prefers_engineering" not in wm: return self._create_question("prefers_engineering", "هل تحب فك وتركيب الأشياء وفهم آلية عمل الماكينات؟")
            if "prefers_it" not in wm: return self._create_question("prefers_it", "هل تجد متعتك في استخدام الحاسوب والتعامل مع البرمجيات؟")
            if wm.get("prefers_medicine") == False and wm.get("prefers_engineering") == False and wm.get("prefers_it") == False:
                if "prefers_arts" not in wm: return self._create_question("prefers_arts", "هل لديك شغف بالرسم، التلوين، أو التصميم البصري؟")
                if "prefers_humanities" not in wm: return self._create_question("prefers_humanities", "هل تميل للحقوق والقانون وفهم السلوك البشري؟")
        elif path == "فني":
            if "prefers_industrial" not in wm: return self._create_question("prefers_industrial", "هل تستهويك الكهرباء، النجارة، أو صيانة السيارات؟")
            if "prefers_commercial" not in wm: return self._create_question("prefers_commercial", "هل تحب تنظيم الحسابات والعمل المكتبي؟")
            if "prefers_agricultural" not in wm: return self._create_question("prefers_agricultural", "هل تحب العمل في التربة والنباتات؟")
            if wm.get("gender") == "female" and "prefers_feminine" not in wm:
                return self._create_question("prefers_feminine", "هل تهتمين بتصميم الأزياء والتدبير المنزلي؟")

        # المرحلة 3: التحقق (3 أسئلة لكل مادة تخصص)
        meyul = wm.get("meyul")
        if meyul == "أحياء/طب":
            if "sci_q1" not in wm: return self._create_question("sci_q1", "هل كانت درجتك في مادة (العلوم الطبيعية) بالمتوسطة عالية؟")
            if "sci_q2" not in wm: return self._create_question("sci_q2", "هل كنت تستمتع بإجراء التجارب العلمية في المختبر؟")
            if "sci_q3" not in wm: return self._create_question("sci_q3", "هل تجد سهولة في فهم وحفظ المصطلحات العلمية المعقدة؟")
        
        elif meyul == "هندسة":
            if "eng_q1" not in wm: return self._create_question("eng_q1", "هل حصلت على درجات متميزة في (الرياضيات) بالمتوسطة؟")
            if "eng_q2" not in wm: return self._create_question("eng_q2", "هل كانت مادة (التربية التقنية) من المواد المفضلة لديك؟")
            if "eng_q3" not in wm: return self._create_question("eng_q3", "هل تبرع في حل المسائل المنطقية والهندسية المعقدة؟")

        elif meyul == "علوم حاسوب":
            if "it_q1" not in wm: return self._create_question("it_q1", "هل كانت درجاتك في (تكنولوجيا المعلومات) عالية جداً؟")
            if "it_q2" not in wm: return self._create_question("it_q2", "هل تقضي وقتاً طويلاً في استكشاف البرامج وكيفية عملها؟")
            if "it_q3" not in wm: return self._create_question("it_q3", "هل تمتلك مهارة الصبر عند التعامل مع أعطال الأجهزة والبرامج؟")

        elif meyul == "فنون وتصميم":
            if "art_q1" not in wm: return self._create_question("art_q1", "هل كانت درجتك في (التربية الفنية) متميزة دائماً؟")
            if "art_q2" not in wm: return self._create_question("art_q2", "هل تشارك في المسابقات الفنية أو تملك معرضاً لأعمالك؟")
            if "art_q3" not in wm: return self._create_question("art_q3", "هل تجد متعتك في تحويل الأفكار إلى تصاميم مرئية وجذابة؟")

        elif meyul == "حقوق/إنسانيات":
            if "hum_q1" not in wm: return self._create_question("hum_q1", "هل كنت متفوقاً في مادتي (التاريخ والجغرافيا) بالمتوسطة؟")
            if "hum_q2" not in wm: return self._create_question("hum_q2", "هل تحب القراءة في مجالات القانون، السياسة، أو علم النفس؟")
            if "hum_q3" not in wm: return self._create_question("hum_q3", "هل تمتلك مهارات قوية في الإقناع والمناظرة الأدبية؟")

        elif meyul == "فني صناعي":
            if "ind_q1" not in wm: return self._create_question("ind_q1", "هل مهاراتك اليدوية في فك وتركيب الأجهزة متميزة؟")
            if "ind_q2" not in wm: return self._create_question("ind_q2", "هل كانت درجاتك في (التربية التقنية) عالية؟")
            if "ind_q3" not in wm: return self._create_question("ind_q3", "هل تفضل العمل الميداني في الورش على الجلوس في المكاتب؟")

        elif meyul == "فني تجاري":
            if "com_q1" not in wm: return self._create_question("com_q1", "هل أنت دقيق جداً في الحسابات والأرقام؟")
            if "com_q2" not in wm: return self._create_question("com_q2", "هل كانت درجتك في (الرياضيات) بالمتوسطة جيدة؟")
            if "com_q3" not in wm: return self._create_question("com_q3", "هل تحب تنظيم الأوراق والبيانات وترتيبها بشكل دقيق؟")

        elif meyul == "فني زراعي":
            if "agr_q1" not in wm: return self._create_question("agr_q1", "هل حصلت على درجات جيدة في مادة (العلوم) بالمتوسطة؟")
            if "agr_q2" not in wm: return self._create_question("agr_q2", "هل تحب العناية بالنباتات والتعرف على أنواع التربة؟")
            if "agr_q3" not in wm: return self._create_question("agr_q3", "هل تستهويك فكرة تطوير مشاريع زراعية تقنية حديثة؟")

        elif meyul == "فني نسوي":
            if "fem_q1" not in wm: return self._create_question("fem_q1", "هل لديك موهبة في الرسم أو الحياكة أو التصميم؟")
            if "fem_q2" not in wm: return self._create_question("fem_q2", "هل كانت درجتك في (التربية الفنية) متميزة؟")
            if "fem_q3" not in wm: return self._create_question("fem_q3", "هل تحبين ابتكار تصاميم جديدة للملابس أو الديكور؟")

        return {"status": "error", "message": "لم نتمكن من الوصول لنتيجة قطعية؛ يرجى التأكد من الميول والتحصيل."}

    def _create_question(self, fact, prompt, q_type="boolean"):
        choices = {
            "gender": [{"label": "ذكر", "value": "male"}, {"label": "أنثى", "value": "female"}],
            "grade": [{"label": "الأول ثانوي", "value": "1st_secondary"}, {"label": "الثالث ثانوي", "value": "3rd_secondary"}],
            "path": [{"label": "أكاديمي", "value": "أكاديمي"}, {"label": "فني", "value": "فني"}]
        }
        return {"status": "question", "fact": fact, "prompt": prompt, "type": q_type, "options": choices.get(fact, [])}

    def backward_chaining(self, facts, goal_fact, goal_value):
        return self.run_inference(facts)

system = ExpertSystem()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/infer", methods=["POST"])
def infer():
    return jsonify(system.run_inference(request.json.get("facts", {})))

@app.route("/api/verify_goal", methods=["POST"])
def verify_goal():
    return jsonify(system.run_inference(request.json.get("facts", {})))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
