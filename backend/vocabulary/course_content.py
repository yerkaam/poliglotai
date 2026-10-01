"""Lessons, checks and words of the 16 course steps.

Our own wording and examples. As with seed.py, the Kazakh texts must be checked by a native-speaking teacher
before launch; the methodologist can then edit everything in the admin (Course steps, Vocabulary).

Each step: lesson blocks (title, short rule, examples), a check of 6–8 exercises ("choice" with one right option
or "input" with accepted answers), the grammar the AI tutor may use once the step is done, and the step's words:
(word, translation_kk, past_form, example_en, example_kk, is_verb).
"""


def ex(en, kk):
    return {"en": en, "kk": kk}


def block(title_kk, text_kk, *examples):
    return {"title_kk": title_kk, "text_kk": text_kk, "examples": list(examples)}


def choice(prompt, prompt_kk, options, answer):
    assert answer in options, (prompt, answer)
    return {"type": "choice", "prompt": prompt, "prompt_kk": prompt_kk, "options": options, "answer": answer}


def typed(prompt, prompt_kk, *answers):
    return {"type": "input", "prompt": prompt, "prompt_kk": prompt_kk, "answers": list(answers)}


def word(w, kk, example_en="", example_kk="", past="", verb=False):
    return (w, kk, past, example_en, example_kk, verb)


STEPS = {
    1: {
        "grammar_en": "",
        "lesson": [
            block(
                "Бір етістік — тоғыз форма",
                "Кесте үш шақтан (келер, осы, өткен) және үш формадан (сұрақ, болымды, болымсыз) тұрады. "
                "Көмекші сөздер: келер шақта will / won't, осы шақта do / does / don't / doesn't, "
                "өткен шақта did / didn't.",
                ex("Will you work? — I will work. — I won't work.", "Жұмыс істейсің бе? — Істеймін. — Істемеймін."),
                ex("Do you work? — I work. — I don't work.", "Жұмыс істейсің бе? — Істеймін. — Істемеймін."),
                ex("Did you work? — I worked. — I didn't work.", "Жұмыс істедің бе? — Істедім. — Істемедім."),
            ),
            block(
                "he / she: -s жалғауы",
                "Осы шақтың болымды формасында he, she үшін етістікке -s (-es) жалғанады. "
                "Сұрақ пен болымсызда жалғаудың орнына does / doesn't тұрады, етістік бастапқы формада қалады.",
                ex("She works in a bank.", "Ол банкте жұмыс істейді."),
                ex("Does she work? — She doesn't work.", "Ол жұмыс істей ме? — Ол жұмыс істемейді."),
            ),
            block(
                "did-тен кейін — бастапқы форма",
                "Өткен шақтың болымды формасында етістік өзгереді: дұрыс етістікке -ed, бұрыс етістіктің өз формасы "
                "бар (go → went). Ал did / didn't тұрса, етістік бастапқы формада қалады.",
                ex("I went home. — Did you go home? — I didn't go home.", "Үйге бардым. — Үйге бардың ба? — Бармадым."),
            ),
        ],
        "exercises": [
            choice("___ she like tea?", "Ол шай ұната ма?", ["Do", "Does", "Did"], "Does"),
            choice("They ___ to the cinema yesterday.", "Олар кеше киноға барды.", ["go", "went", "goes"], "went"),
            choice("I ___ call you tomorrow.", "Ертең саған қоңырау шаламын.", ["will", "do", "did"], "will"),
            choice("He ___ not speak French.", "Ол французша сөйлемейді.", ["do", "does", "did"], "does"),
            typed(
                "Past, negative: I / buy / a car", "Өткен шақ, болымсыз: Мен көлік сатып алмадым.", "I didn't buy a car"
            ),
            typed("Present, affirmative: she / watch / TV", "Осы шақ, болымды: Ол теледидар көреді.", "She watches TV"),
            typed("Future, question: you / help / me", "Келер шақ, сұрақ: Маған көмектесесің бе?", "Will you help me"),
        ],
        "words": [],
    },
    2: {
        "grammar_en": "question words (what, where, when, why, who, how, which, whose, how much, how many) "
        "at the start of questions",
        "lesson": [
            block(
                "Сұраулы сөз — сөйлемнің басында",
                "Сұраулы сөз кестедегі сұрақтың алдына қойылады: сұраулы сөз + will / do / does / did + кім + етістік.",
                ex("Where do you live?", "Қайда тұрасың?"),
                ex("What did you buy?", "Не сатып алдың?"),
                ex("When will they come?", "Олар қашан келеді?"),
            ),
            block(
                "who — кім?",
                "Егер who сұрақтың өзі «кім?» болса (бастауыш), көмекші сөз керек емес: Who lives here?",
                ex("Who lives here?", "Мұнда кім тұрады?"),
                ex("Who did you see?", "Кімді көрдің?"),
            ),
            block(
                "how much / how many",
                "how many — саналатын заттар үшін (books, people), how much — саналмайтын заттар мен баға үшін "
                "(water, money).",
                ex("How many books do you have?", "Сенде неше кітап бар?"),
                ex("How much does it cost?", "Бұл қанша тұрады?"),
            ),
        ],
        "exercises": [
            choice("___ do you live? — In Almaty.", "Қайда тұрасың? — Алматыда.", ["What", "Where", "When"], "Where"),
            choice(
                "___ did you call me? — Because I need help.",
                "Маған неге қоңырау шалдың?",
                ["Why", "Who", "How"],
                "Why",
            ),
            choice(
                "___ books do you read every month?",
                "Айына неше кітап оқисың?",
                ["How much", "How many", "Which"],
                "How many",
            ),
            choice("___ lives in this house?", "Бұл үйде кім тұрады?", ["Who", "What", "Whose"], "Who"),
            choice("___ phone is this? — It's Asel's.", "Бұл кімнің телефоны?", ["Who", "Whose", "Which"], "Whose"),
            typed("Ask: where / you / work (present)", "Сұраңыз: Қайда жұмыс істейсің?", "Where do you work"),
            typed("Ask: what / she / buy (past)", "Сұраңыз: Ол не сатып алды?", "What did she buy"),
        ],
        "words": [
            word("what", "не, қандай", "What do you want?", "Сен не қалайсың?"),
            word("where", "қайда", "Where do you live?", "Сен қайда тұрасың?"),
            word("when", "қашан", "When do you start work?", "Жұмысты қашан бастайсың?"),
            word("why", "неге, неліктен", "Why do you study English?", "Сен ағылшын тілін неге оқисың?"),
            word("who", "кім", "Who is your teacher?", "Сенің мұғалімің кім?"),
            word("how", "қалай", "How do you go to work?", "Жұмысқа қалай барасың?"),
            word("which", "қайсы", "Which bus do you take?", "Қай автобусқа отырасың?"),
            word("whose", "кімнің", "Whose bag is this?", "Бұл кімнің сөмкесі?"),
            word("how much", "қанша (баға, саналмайтын зат)", "How much is it?", "Бұл қанша тұрады?"),
            word("how many", "неше, қанша (саналатын зат)", "How many children do you have?", "Неше балаң бар?"),
        ],
    },
    3: {
        "grammar_en": "the verb to be: am / is / are, was / were, will be, with adjectives and places",
        "lesson": [
            block(
                "to be — «болу», «-мын, -сың, -ды»",
                "Қазақшада «Мен дәрігермін» — бір сөз, ағылшыншада етістік керек: I am a doctor. "
                "Осы шақта: I am, he / she / it is, you / we / they are.",
                ex("I am tired.", "Мен шаршадым."),
                ex("She is a teacher.", "Ол — мұғалім."),
                ex("We are at home.", "Біз үйдеміз."),
            ),
            block(
                "Сұрақ пен болымсыз — do керек емес",
                "to be өзі көмекші сөз сияқты: сұрақта алға шығады, болымсызда not жалғанады.",
                ex("Are you busy? — No, I am not busy.", "Қолың бос емес пе? — Жоқ, қолым бос."),
                ex("Is he at work? — He isn't at work.", "Ол жұмыста ма? — Ол жұмыста емес."),
            ),
            block(
                "Өткен және келер шақ",
                "Өткен шақта: I / he / she / it was, you / we / they were. Келер шақта барлығына will be.",
                ex("I was at home yesterday.", "Кеше үйде болдым."),
                ex("Were they late?", "Олар кешікті ме?"),
                ex("It will be cold tomorrow.", "Ертең суық болады."),
            ),
        ],
        "exercises": [
            choice("She ___ a doctor.", "Ол — дәрігер.", ["am", "is", "are"], "is"),
            choice("We ___ at home yesterday.", "Біз кеше үйде болдық.", ["was", "were", "are"], "were"),
            choice("___ you hungry?", "Қарның аш па?", ["Do", "Are", "Is"], "Are"),
            choice("I ___ late tomorrow.", "Ертең кешігемін.", ["will be", "am", "was"], "will be"),
            choice("He ___ at work now.", "Ол қазір жұмыста емес.", ["isn't", "doesn't", "aren't"], "isn't"),
            typed("They / be / happy (present)", "Олар бақытты.", "They are happy"),
            typed("I / be / tired (past)", "Мен шаршадым (өткен шақ).", "I was tired"),
        ],
        "words": [
            word("be", "болу", "Be careful!", "Абай бол!"),
            word("busy", "бос емес, қолы тимейді", "I am busy today.", "Мен бүгін бос емеспін."),
            word("tired", "шаршаған", "She is tired after work.", "Ол жұмыстан кейін шаршаған."),
            word("happy", "бақытты, қуанышты", "We are happy to see you.", "Сені көргенімізге қуаныштымыз."),
            word("hungry", "аш, қарны ашқан", "Are you hungry?", "Қарның аш па?"),
            word("ready", "дайын", "Dinner is ready.", "Кешкі ас дайын."),
            word("late", "кеш, кешіккен", "Sorry, I am late.", "Кешіріңіз, кешіктім."),
            word("angry", "ашулы", "He was angry yesterday.", "Ол кеше ашулы болды."),
            word("sick", "ауру, науқас", "My son is sick.", "Ұлым ауырып жатыр."),
            word("free", "бос; тегін", "Are you free tonight?", "Бүгін кешке босысың ба?"),
        ],
    },
    4: {
        "grammar_en": "prepositions of place, time and direction: in, on, at, to, from, with, for, under, near, "
        "between, before, after",
        "lesson": [
            block(
                "Орын: in, on, at",
                "in — ішінде (in the box, in Almaty), on — үстінде (on the table), at — нақты нүктеде "
                "(at home, at work, at the bus stop). Қазақшада бұлардың көбі -да / -де жалғауы.",
                ex("The keys are in my bag.", "Кілттер сөмкемде."),
                ex("The book is on the table.", "Кітап үстелдің үстінде."),
                ex("I am at work.", "Мен жұмыстамын."),
            ),
            block(
                "Уақыт: in, on, at",
                "at — сағат (at 7 o'clock), on — күн (on Monday), "
                "in — ай, жыл, тәулік бөлігі (in May, in the morning).",
                ex("I get up at seven.", "Мен сағат жетіде тұрамын."),
                ex("We meet on Friday.", "Біз жұма күні кездесеміз."),
                ex("She was born in 1995.", "Ол 1995 жылы туған."),
            ),
            block(
                "Бағыт: to, from",
                "to — қайда? (-ға / -ге), from — қайдан? (-дан / -ден).",
                ex("I go to school.", "Мен мектепке барамын."),
                ex("He is from Shymkent.", "Ол Шымкенттен."),
            ),
        ],
        "exercises": [
            choice("I live ___ Astana.", "Мен Астанада тұрамын.", ["in", "on", "at"], "in"),
            choice("The phone is ___ the table.", "Телефон үстелдің үстінде.", ["in", "on", "at"], "on"),
            choice("We start work ___ nine o'clock.", "Біз жұмысты сағат тоғызда бастаймыз.", ["in", "on", "at"], "at"),
            choice("My birthday is ___ June.", "Туған күнім маусымда.", ["in", "on", "at"], "in"),
            choice("I go ___ work by bus.", "Жұмысқа автобуспен барамын.", ["to", "from", "at"], "to"),
            choice("She is ___ Taraz.", "Ол Тараздан.", ["to", "from", "in"], "from"),
            typed("Translate: after work", "Аударыңыз: жұмыстан кейін", "after work"),
        ],
        "words": [
            word("in", "ішінде; -да / -де (қала, ай, жыл)", "The milk is in the fridge.", "Сүт тоңазытқышта."),
            word("on", "үстінде; -да / -де (күн)", "Your cup is on the table.", "Кесең үстелдің үстінде."),
            word("at", "-да / -де (нақты орын, сағат)", "I am at home.", "Мен үйдемін."),
            word("to", "-ға / -ге (бағыт)", "We go to the park.", "Біз саябаққа барамыз."),
            word("from", "-дан / -ден", "I am from Kazakhstan.", "Мен Қазақстанданмын."),
            word("with", "-мен, бірге", "I live with my parents.", "Мен ата-анаммен бірге тұрамын."),
            word("for", "үшін", "This gift is for you.", "Бұл сыйлық сен үшін."),
            word("under", "астында", "The cat is under the bed.", "Мысық төсектің астында."),
            word("near", "жанында, жақын", "We live near the school.", "Біз мектептің жанында тұрамыз."),
            word(
                "between", "арасында", "The bank is between the shop and the cafe.", "Банк дүкен мен кафенің арасында."
            ),
            word("before", "дейін, бұрын", "Wash your hands before dinner.", "Тамақтың алдында қолыңды жу."),
            word("after", "кейін", "I read after work.", "Мен жұмыстан кейін кітап оқимын."),
        ],
    },
    5: {
        "grammar_en": "possessive determiners and pronouns: my, your, his, her, its, our, their, mine",
        "lesson": [
            block(
                "Кімнің?",
                "Қазақшада тәуелдік жалғау қолданылады (кітабым), ағылшыншада сөздің алдына сөз қойылады: my book. "
                "I → my, you → your, he → his, she → her, it → its, we → our, they → their.",
                ex("My name is Aliya.", "Менің атым — Әлия."),
                ex("This is his car.", "Бұл — оның көлігі (ер адам)."),
                ex("Their house is big.", "Олардың үйі үлкен."),
            ),
            block(
                "his пен her",
                "Қазақшада екеуі де «оның», ағылшыншада иесінің жынысына қарай: ер адам — his, әйел — her.",
                ex("Asel loves her job.", "Әсел өз жұмысын жақсы көреді."),
                ex("Daniyar called his mother.", "Данияр анасына қоңырау шалды."),
            ),
            block(
                "mine — менікі",
                "Зат есімсіз «менікі» деу үшін mine, yours, ours, theirs қолданылады.",
                ex("This bag is mine.", "Бұл сөмке менікі."),
            ),
        ],
        "exercises": [
            choice("I love ___ city.", "Мен өз қаламды жақсы көремін.", ["my", "your", "our"], "my"),
            choice("Aigerim called ___ friend.", "Айгерім досына қоңырау шалды.", ["his", "her", "its"], "her"),
            choice("Arman lost ___ keys.", "Арман кілттерін жоғалтты.", ["his", "her", "their"], "his"),
            choice(
                "We visit ___ grandparents on Sunday.",
                "Біз жексенбіде ата-әжемізге барамыз.",
                ["their", "our", "your"],
                "our",
            ),
            choice("The children play with ___ dog.", "Балалар иттерімен ойнайды.", ["their", "his", "our"], "their"),
            choice(
                "Is this phone ___? — Yes, it's my phone.", "Бұл телефон сенікі ме?", ["you", "yours", "your"], "yours"
            ),
            typed("Translate: our teacher", "Аударыңыз: біздің мұғалім", "our teacher"),
        ],
        "words": [
            word("my", "менің", "My brother is a doctor.", "Менің ағам — дәрігер."),
            word("your", "сенің, сіздің", "What is your name?", "Сіздің атыңыз кім?"),
            word("his", "оның (ер адам)", "His car is new.", "Оның көлігі жаңа."),
            word("her", "оның (әйел)", "Her sister lives in London.", "Оның әпкесі Лондонда тұрады."),
            word("its", "оның (зат, жануар)", "The cat likes its bed.", "Мысық өз төсегін ұнатады."),
            word("our", "біздің", "Our flat is small.", "Біздің пәтеріміз шағын."),
            word("their", "олардың", "Their children go to school.", "Олардың балалары мектепке барады."),
            word("mine", "менікі", "This coffee is mine.", "Бұл кофе менікі."),
        ],
    },
    6: {
        "grammar_en": "the past forms of common irregular verbs",
        "description_kk": "Жиі қолданылатын тағы 40-тан астам бұрыс етістік: өткен шақ формалары",
        "lesson": [
            block(
                "Бұрыс етістік дегеніміз не?",
                "Дұрыс етістіктер өткен шақта -ed алады (work → worked). Бұрыс етістіктердің өз формасы бар, оны "
                "жаттау керек: go → went, buy → bought. Ең жиі қолданылатын етістіктердің көбі — бұрыс.",
                ex("I met my friend yesterday.", "Кеше досымды кездестірдім."),
                ex("She taught English.", "Ол ағылшын тілін оқытты."),
            ),
            block(
                "Ұқсас топтар — жаттауға оңай",
                "Кейбір етістіктер бірдей өзгереді: bring → brought, buy → bought, think → thought, teach → taught; "
                "sleep → slept, keep → kept, meet → met; put, cut — мүлде өзгермейді.",
                ex("He brought a cake.", "Ол торт әкелді."),
                ex("I slept well.", "Жақсы ұйықтадым."),
                ex("She put the book on the table.", "Ол кітапты үстелге қойды."),
            ),
            block(
                "did-тен кейін — бастапқы форма",
                "Сұрақ пен болымсызда бұрыс етістік те бастапқы формаға оралады.",
                ex("Did you sleep well? — I didn't sleep.", "Жақсы ұйықтадың ба? — Ұйықтамадым."),
            ),
        ],
        "exercises": [
            choice(
                "I ___ a new jacket last week.",
                "Өткен аптада жаңа күртеше сатып алдым.",
                ["buyed", "bought", "buy"],
                "bought",
            ),
            choice(
                "We ___ our teacher in the street.",
                "Мұғалімімізді көшеде кездестірдік.",
                ["meeted", "met", "meet"],
                "met",
            ),
            choice("Did you ___ the news?", "Жаңалықты естідің бе?", ["hear", "heard", "heared"], "hear"),
            choice(
                "She ___ the window because it was cold.",
                "Суық болғандықтан ол терезені жапты.",
                ["closed", "close", "closen"],
                "closed",
            ),
            typed("Past of: sleep", "sleep — өткен шақ формасы", "slept"),
            typed("Past of: teach", "teach — өткен шақ формасы", "taught"),
            typed("Past of: put", "put — өткен шақ формасы", "put"),
            typed("Past, affirmative: I / forget / my keys", "Мен кілттерімді ұмыттым.", "I forgot my keys"),
        ],
        "words": [
            word("become", "болу, айналу", "She became a doctor.", "Ол дәрігер болды.", "became", True),
            word(
                "begin", "бастау, басталу", "The lesson began at nine.", "Сабақ сағат тоғызда басталды.", "began", True
            ),
            word("break", "сындыру", "I broke my phone.", "Телефонымды сындырып алдым.", "broke", True),
            word("bring", "әкелу", "He brought flowers.", "Ол гүл әкелді.", "brought", True),
            word("build", "салу, тұрғызу", "They built a new school.", "Олар жаңа мектеп салды.", "built", True),
            word("choose", "таңдау", "I chose the red one.", "Мен қызылын таңдадым.", "chose", True),
            word("cut", "кесу", "She cut the bread.", "Ол нанды кесті.", "cut", True),
            word(
                "drive",
                "көлік жүргізу",
                "My father drove us to the airport.",
                "Әкем бізді әуежайға апарды.",
                "drove",
                True,
            ),
            word("fall", "құлау", "The child fell but didn't cry.", "Бала құлады, бірақ жыламады.", "fell", True),
            word("feel", "сезіну", "I felt tired yesterday.", "Кеше өзімді шаршаңқы сезіндім.", "felt", True),
            word("fly", "ұшу", "We flew to Istanbul.", "Біз Стамбұлға ұшып бардық.", "flew", True),
            word("forget", "ұмыту", "I forgot her name.", "Мен оның атын ұмытып қалдым.", "forgot", True),
            word("grow", "өсу, өсіру", "My grandfather grew apples.", "Атам алма өсірді.", "grew", True),
            word("hear", "есту", "Did you hear me?", "Мені естідің бе?", "heard", True),
            word("hold", "ұстау", "She held the baby.", "Ол сәбиді құшағына алды.", "held", True),
            word("keep", "сақтау, ұстап тұру", "He kept the money.", "Ол ақшаны сақтады.", "kept", True),
            word("lose", "жоғалту; ұтылу", "I lost my keys.", "Кілттерімді жоғалтып алдым.", "lost", True),
            word("meet", "кездесу, танысу", "We met in Almaty.", "Біз Алматыда таныстық.", "met", True),
            word("pay", "төлеу", "I paid by card.", "Мен картамен төледім.", "paid", True),
            word("put", "қою, салу", "Put your bag here.", "Сөмкеңді осында қой.", "put", True),
            word("run", "жүгіру", "He ran to the bus.", "Ол автобусқа жүгірді.", "ran", True),
            word("sell", "сату", "They sold their car.", "Олар көліктерін сатты.", "sold", True),
            word("send", "жіберу", "I sent you a message.", "Саған хабарлама жібердім.", "sent", True),
            word("sing", "ән айту", "She sang a Kazakh song.", "Ол қазақ әнін айтты.", "sang", True),
            word("sit", "отыру", "We sat in the garden.", "Біз бақта отырдық.", "sat", True),
            word("sleep", "ұйықтау", "The baby slept all night.", "Сәби түні бойы ұйықтады.", "slept", True),
            word(
                "spend",
                "жұмсау; өткізу (уақыт)",
                "We spent the summer in the mountains.",
                "Жазды тауда өткіздік.",
                "spent",
                True,
            ),
            word("stand", "тұру (аяқта)", "They stood at the door.", "Олар есіктің алдында тұрды.", "stood", True),
            word("swim", "жүзу", "We swam in the lake.", "Біз көлде жүздік.", "swam", True),
            word(
                "teach", "оқыту, үйрету", "My mother teaches maths.", "Анам математикадан сабақ береді.", "taught", True
            ),
            word(
                "understand", "түсіну", "I didn't understand the question.", "Сұрақты түсінбедім.", "understood", True
            ),
            word("wake", "ояну, ояту", "I woke at six.", "Мен сағат алтыда ояндым.", "woke", True),
            word("wear", "кию (киіп жүру)", "She wore a blue dress.", "Ол көк көйлек киді.", "wore", True),
            word("win", "жеңу, ұтып алу", "Our team won the game.", "Біздің команда ойында жеңді.", "won", True),
            word("catch", "ұстап алу; үлгеру", "I caught the last bus.", "Соңғы автобусқа үлгердім.", "caught", True),
            word("draw", "сурет салу", "The child drew a horse.", "Бала ат суретін салды.", "drew", True),
            word("hide", "жасыру, тығылу", "The cat hid under the bed.", "Мысық төсектің астына тығылды.", "hid", True),
            word(
                "fight",
                "төбелесу, күресу",
                "The brothers never fought.",
                "Ағайындылар ешқашан төбелеспеді.",
                "fought",
                True,
            ),
            word("lend", "қарызға беру", "Can you lend me a pen?", "Маған қалам бере тұрасың ба?", "lent", True),
            word("ride", "міну (ат, велосипед)", "I rode a horse in the village.", "Ауылда ат міндім.", "rode", True),
        ],
    },
    7: {
        "grammar_en": "modal verbs can / can't, could, must, should, may, would like",
        "lesson": [
            block(
                "Модаль етістік + бастапқы форма",
                "can (істей аламын), must (міндеттімін), should (істегенім жөн), may (болады, мүмкін). "
                "Модаль етістіктен кейін етістік әрқашан бастапқы формада, he / she үшін -s жалғанбайды.",
                ex("I can swim.", "Мен жүзе аламын."),
                ex("She can speak English.", "Ол ағылшынша сөйлей алады."),
                ex("You should drink more water.", "Көбірек су ішкенің жөн."),
            ),
            block(
                "Сұрақ пен болымсыз — do керек емес",
                "Модаль етістік өзі алға шығады немесе not қабылдайды: can't, mustn't, shouldn't.",
                ex("Can you help me?", "Маған көмектесе аласың ба?"),
                ex("You mustn't smoke here.", "Мұнда темекі шегуге болмайды."),
            ),
            block(
                "Сыпайы өтініш: could, may, would like",
                "Could you…? — сыпайы өтініш, May I…? — рұқсат сұрау, I would like… — «…қалар едім».",
                ex("Could you open the window?", "Терезені ашып жібере аласыз ба?"),
                ex("May I come in?", "Кіруге болады ма?"),
                ex("I would like a cup of tea.", "Бір кесе шай ішер едім."),
            ),
        ],
        "exercises": [
            choice("She ___ play the piano.", "Ол пианинода ойнай алады.", ["can", "cans", "can to"], "can"),
            choice(
                "You ___ wear a seat belt. It's the law.",
                "Қауіпсіздік белдігін тағу міндетті.",
                ["must", "may", "can"],
                "must",
            ),
            choice(
                "You look tired. You ___ go to bed.",
                "Шаршаған көрінесің, ұйықтағаның жөн.",
                ["should", "can't", "may"],
                "should",
            ),
            choice("___ I use your phone?", "Телефоныңызды пайдалануға бола ма?", ["May", "Must", "Should"], "May"),
            choice("He can ___ French.", "Ол французша сөйлей алады.", ["speak", "speaks", "to speak"], "speak"),
            typed("Negative: I / can / drive", "Мен көлік жүргізе алмаймын.", "I can't drive", "I cannot drive"),
            typed(
                "Ask politely: could / you / help / me",
                "Сыпайы сұраңыз: Маған көмектесе аласыз ба?",
                "Could you help me",
            ),
        ],
        "words": [
            word("can", "істей алу, болады", "I can cook plov.", "Мен палау пісіре аламын."),
            word("could", "істей алды; сыпайы өтініш", "Could you repeat that?", "Қайталап жібере аласыз ба?"),
            word("must", "міндетті, керек", "I must go now.", "Қазір кетуім керек."),
            word("should", "жөн, тиіс", "You should see a doctor.", "Дәрігерге қаралғаның жөн."),
            word("may", "болады, рұқсат; мүмкін", "May I sit here?", "Осында отыруға бола ма?"),
            word("would like", "қалар еді", "I would like some water.", "Су ішер едім."),
        ],
    },
    8: {
        "grammar_en": "Present Continuous (am / is / are + -ing) and Past Continuous (was / were + -ing)",
        "lesson": [
            block(
                "Дәл қазір болып жатқан іс",
                "Present Continuous: am / is / are + етістік-ing. «Қазір істеп жатырмын» мағынасы. "
                "Осы шақпен салыстырыңыз: I work (күнде, әдетте) — I am working (дәл қазір).",
                ex("I am reading now.", "Мен қазір оқып отырмын."),
                ex("She is cooking dinner.", "Ол кешкі ас дайындап жатыр."),
                ex("Are they sleeping? — No, they aren't.", "Олар ұйықтап жатыр ма? — Жоқ."),
            ),
            block(
                "Өткенде жүріп жатқан іс",
                "Past Continuous: was / were + -ing. «Сол кезде істеп жатқан едім» мағынасы.",
                ex("I was watching TV at eight.", "Сағат сегізде теледидар көріп отыр едім."),
                ex("What were you doing yesterday evening?", "Кеше кешке не істеп жатыр едің?"),
            ),
            block(
                "-ing жазылуы",
                "write → writing (е түседі), sit → sitting, swim → swimming (дауыссыз екі еселенеді), lie → lying.",
                ex("He is writing a letter.", "Ол хат жазып отыр."),
            ),
        ],
        "exercises": [
            choice("Look! It ___ .", "Қара! Жаңбыр жауып тұр.", ["rains", "is raining", "rain"], "is raining"),
            choice(
                "I usually ___ tea in the morning.",
                "Мен әдетте таңертең шай ішемін.",
                ["drink", "am drinking", "drinking"],
                "drink",
            ),
            choice(
                "They ___ football at 5 p.m. yesterday.",
                "Кеше сағат беске олар футбол ойнап жүрген.",
                ["were playing", "are playing", "was playing"],
                "were playing",
            ),
            choice("She is ___ a book.", "Ол кітап жазып жатыр.", ["writeing", "writing", "writting"], "writing"),
            choice("___ you working now?", "Қазір жұмыс істеп жатырсың ба?", ["Do", "Are", "Is"], "Are"),
            typed(
                "Present Continuous: we / wait / for the bus", "Біз автобус күтіп тұрмыз.", "We are waiting for the bus"
            ),
            typed("Past Continuous: he / sleep", "Ол ұйықтап жатқан.", "He was sleeping"),
        ],
        "words": [
            word("now", "қазір", "I am busy now.", "Мен қазір бос емеспін."),
            word("at the moment", "дәл қазір", "She is working at the moment.", "Ол дәл қазір жұмыс істеп жатыр."),
            word("still", "әлі, әлі де", "He is still sleeping.", "Ол әлі ұйықтап жатыр."),
        ],
    },
    9: {
        "grammar_en": "Present Perfect (have / has + past participle) with already, yet, ever, never, just",
        "lesson": [
            block(
                "Нәтиже маңызды болғанда",
                "Present Perfect: have / has + етістіктің үшінші формасы. Іс қашан болғаны емес, нәтижесі "
                "маңызды: «Кілтімді жоғалтып алдым (қазір кілтім жоқ)».",
                ex("I have lost my keys.", "Кілтімді жоғалтып алдым."),
                ex("She has finished her work.", "Ол жұмысын бітірді."),
            ),
            block(
                "Үшінші форма",
                "Дұрыс етістіктерде ол өткен шақпен бірдей (worked). Бұрыс етістіктердің өз формасы бар: "
                "go → gone, see → seen, do → done, eat → eaten, write → written.",
                ex("Have you ever seen the sea?", "Теңізді бұрын-соңды көрдің бе?"),
                ex("I have never been to London.", "Мен Лондонда ешқашан болған емеспін."),
            ),
            block(
                "Нақты уақыт болса — Past Simple",
                "yesterday, last year, in 2020 сияқты нақты уақыт айтылса, "
                "Present Perfect емес, өткен шақ қолданылады.",
                ex("I have read this book. — I read it last year.", "Бұл кітапты оқығанмын. — Оны өткен жылы оқыдым."),
            ),
        ],
        "exercises": [
            choice(
                "I ___ my homework. Can I go out?",
                "Үй тапсырмасын орындадым. Шығуға бола ма?",
                ["have done", "did", "has done"],
                "have done",
            ),
            choice(
                "She ___ to Paris twice.",
                "Ол Парижде екі рет болды.",
                ["has been", "have been", "was been"],
                "has been",
            ),
            choice("___ you ever eaten horse meat?", "Жылқы етін жеп көрдің бе?", ["Did", "Have", "Has"], "Have"),
            choice("I saw him ___ .", "Мен оны кеше көрдім.", ["yesterday", "ever", "yet"], "yesterday"),
            choice("Have you finished ___ ?", "Бітірдің бе әлі?", ["yet", "already", "never"], "yet"),
            typed("Third form of: write", "write — үшінші форма", "written"),
            typed("Present Perfect: they / buy / a house", "Олар үй сатып алды.", "They have bought a house"),
        ],
        "words": [
            word("already", "әлдеқашан, қазірдің өзінде", "I have already eaten.", "Мен тамақ ішіп қойдым."),
            word("yet", "әлі (сұрақ, болымсыз)", "He hasn't called yet.", "Ол әлі қоңырау шалған жоқ."),
            word("ever", "бұрын-соңды", "Have you ever been to Turkey?", "Түркияда бұрын болдың ба?"),
            word("never", "ешқашан", "I have never tried sushi.", "Суши ешқашан жеп көрмеппін."),
            word("just", "жаңа ғана", "She has just left.", "Ол жаңа ғана кетті."),
        ],
    },
    10: {
        "grammar_en": "comparatives and superlatives (bigger, the biggest, more / the most, better / the best)",
        "lesson": [
            block(
                "-er / the -est",
                "Қысқа сын есімге -er (салыстырмалы шырай) немесе the -est (күшейтпелі шырай) жалғанады. "
                "Салыстырғанда than (-дан / -ден) қолданылады.",
                ex("Almaty is bigger than Taraz.", "Алматы Тараздан үлкен."),
                ex("This is the cheapest phone.", "Бұл — ең арзан телефон."),
            ),
            block(
                "more / the most",
                "Ұзын сын есімдермен more және the most қолданылады: beautiful → more beautiful → the most beautiful.",
                ex("English is more difficult than Turkish for me.", "Мен үшін ағылшын тілі түрік тілінен қиынырақ."),
                ex("It is the most beautiful city.", "Бұл — ең әдемі қала."),
            ),
            block(
                "Ерекше формалар",
                "good → better → the best, bad → worse → the worst.",
                ex("Your English is better now.", "Ағылшын тілің қазір жақсырақ."),
                ex("This is the best day!", "Бұл — ең жақсы күн!"),
            ),
        ],
        "exercises": [
            choice(
                "Astana is ___ than Kokshetau.", "Астана Көкшетаудан үлкен.", ["big", "bigger", "biggest"], "bigger"
            ),
            choice(
                "This is ___ restaurant in the city.",
                "Бұл — қаладағы ең жақсы мейрамхана.",
                ["the best", "the goodest", "better"],
                "the best",
            ),
            choice(
                "Today is ___ than yesterday.",
                "Бүгін кешегіден суығырақ.",
                ["colder", "more cold", "coldest"],
                "colder",
            ),
            choice(
                "This book is ___ than that one.",
                "Бұл кітап анау кітаптан қызықтырақ.",
                ["interestinger", "more interesting", "most interesting"],
                "more interesting",
            ),
            choice("My cold is ___ today.", "Тұмауым бүгін күшейіп кетті.", ["bad", "worse", "worst"], "worse"),
            typed("Comparative of: cheap", "cheap — салыстырмалы шырай", "cheaper"),
            typed("Superlative of: young", "young — күшейтпелі шырай", "the youngest", "youngest"),
        ],
        "words": [
            word("big", "үлкен", "They live in a big house.", "Олар үлкен үйде тұрады."),
            word("small", "кішкентай, шағын", "I have a small car.", "Менің шағын көлігім бар."),
            word("good", "жақсы", "It's a good idea.", "Бұл жақсы ой."),
            word("bad", "жаман", "The weather is bad today.", "Бүгін ауа райы жаман."),
            word("long", "ұзын, ұзақ", "It was a long day.", "Ұзақ күн болды."),
            word("short", "қысқа", "Write a short answer.", "Қысқа жауап жаз."),
            word("cheap", "арзан", "Bread is cheap here.", "Мұнда нан арзан."),
            word("expensive", "қымбат", "This watch is expensive.", "Бұл сағат қымбат."),
            word("fast", "жылдам", "The train is fast.", "Пойыз жылдам жүреді."),
            word("slow", "баяу", "The internet is slow today.", "Бүгін интернет баяу."),
            word("old", "ескі; кәрі", "My phone is old.", "Телефоным ескі."),
            word("young", "жас", "Her parents are young.", "Оның ата-анасы жас."),
            word("beautiful", "әдемі", "What a beautiful view!", "Қандай әдемі көрініс!"),
            word("easy", "оңай", "The test was easy.", "Тест оңай болды."),
            word("difficult", "қиын", "This question is difficult.", "Бұл сұрақ қиын."),
        ],
    },
    11: {
        "grammar_en": "numbers, days of the week, months, dates and telling the time",
        "lesson": [
            block(
                "Сандар",
                "1–10: one, two, three, four, five, six, seven, eight, nine, ten. 11 — eleven, 12 — twelve, "
                "13–19: -teen (thirteen), ондықтар: -ty (twenty, thirty). 100 — a hundred, 1000 — a thousand.",
                ex("I have two brothers.", "Менің екі ағам бар."),
                ex("It costs twenty dollars.", "Бұл жиырма доллар тұрады."),
            ),
            block(
                "Күндер мен айлар — бас әріппен",
                "Апта күндері мен айлар ағылшыншада бас әріппен жазылады. Күнмен on, аймен in қолданылады.",
                ex("See you on Monday.", "Дүйсенбіде көріскенше."),
                ex("Nauryz is in March.", "Наурыз мерекесі наурыз айында."),
            ),
            block(
                "Сағат",
                "It's seven o'clock — сағат жеті. It's half past six — алты жарым. It's a quarter to nine — тоғызға "
                "он бес минут қалды.",
                ex("What time is it? — It's ten o'clock.", "Сағат неше? — Сағат он."),
            ),
        ],
        "exercises": [
            choice("7 + 5 = ?", "Жеті қосу бес", ["eleven", "twelve", "twenty"], "twelve"),
            choice(
                "The day after Monday is ___ .", "Дүйсенбіден кейінгі күн", ["Sunday", "Tuesday", "Thursday"], "Tuesday"
            ),
            choice(
                "The first month of the year is ___ .", "Жылдың бірінші айы", ["January", "June", "March"], "January"
            ),
            choice("My birthday is ___ May.", "Туған күнім мамырда.", ["on", "in", "at"], "in"),
            choice("6:30 — It's ___ six.", "Алты жарым", ["half past", "quarter to", "o'clock"], "half past"),
            typed("Write the number: 3", "Санды сөзбен жазыңыз: 3", "three"),
            typed("The day before Sunday", "Жексенбінің алдындағы күн", "Saturday"),
        ],
        "words": [
            word("one", "бір"),
            word("two", "екі"),
            word("three", "үш"),
            word("four", "төрт"),
            word("five", "бес"),
            word("six", "алты"),
            word("seven", "жеті"),
            word("eight", "сегіз"),
            word("nine", "тоғыз"),
            word("ten", "он"),
            word("twelve", "он екі"),
            word("twenty", "жиырма"),
            word("hundred", "жүз", "A hundred people came.", "Жүз адам келді."),
            word("thousand", "мың", "It costs a thousand tenge.", "Бұл мың теңге тұрады."),
            word("Monday", "дүйсенбі", "I work on Monday.", "Мен дүйсенбіде жұмыс істеймін."),
            word("Tuesday", "сейсенбі"),
            word("Wednesday", "сәрсенбі"),
            word("Thursday", "бейсенбі"),
            word("Friday", "жұма"),
            word("Saturday", "сенбі"),
            word("Sunday", "жексенбі", "We rest on Sunday.", "Біз жексенбіде демаламыз."),
            word("January", "қаңтар"),
            word("February", "ақпан"),
            word("March", "наурыз"),
            word("April", "сәуір"),
            word("May", "мамыр"),
            word("June", "маусым"),
            word("July", "шілде"),
            word("August", "тамыз"),
            word("September", "қыркүйек"),
            word("October", "қазан"),
            word("November", "қараша"),
            word("December", "желтоқсан"),
            word("week", "апта", "I go to the gym three times a week.", "Аптасына үш рет спортзалға барамын."),
            word("month", "ай", "She visits us every month.", "Ол бізге ай сайын келеді."),
            word("year", "жыл", "Happy New Year!", "Жаңа жылың құтты болсын!"),
        ],
    },
    12: {
        "grammar_en": "the simple passive: is / are + past participle, was / were + past participle",
        "lesson": [
            block(
                "Ырықсыз етіс",
                "Істі кім істегені емес, іс өзі маңызды болғанда: to be + үшінші форма. "
                "Қазақшада -ылды / -ілді, -нды жұрнақтары сияқты.",
                ex("This car is made in Kazakhstan.", "Бұл көлік Қазақстанда жасалады."),
                ex("The school was built in 1980.", "Мектеп 1980 жылы салынды."),
            ),
            block(
                "by — кім арқылы",
                "Істі кім істегенін айту үшін by қолданылады.",
                ex("Abai's poems are read by everyone.", "Абайдың өлеңдерін бәрі оқиды."),
                ex("The letter was written by my grandfather.", "Хатты атам жазған."),
            ),
        ],
        "exercises": [
            choice(
                "English ___ all over the world.",
                "Ағылшын тілінде бүкіл әлемде сөйлейді.",
                ["is spoken", "speaks", "is speak"],
                "is spoken",
            ),
            choice(
                "The house ___ last year.", "Үй өткен жылы салынды.", ["was built", "is built", "built"], "was built"
            ),
            choice(
                "These phones ___ in China.",
                "Бұл телефондар Қытайда жасалады.",
                ["are made", "is made", "make"],
                "are made",
            ),
            choice("The cake was made ___ my sister.", "Тортты әпкем пісірген.", ["by", "from", "with"], "by"),
            typed("Passive, present: tea / grow / in India", "Шай Үндістанда өсіріледі.", "Tea is grown in India"),
            typed("Passive, past: the window / break", "Терезе сынды (сындырылды).", "The window was broken"),
        ],
        "words": [],
    },
    13: {
        "grammar_en": "first conditional: If + present, will + verb; unless; otherwise",
        "lesson": [
            block(
                "Егер … болса, … болады",
                "Шартты сөйлем: If + осы шақ, will + етістік. If бөлігінде will қолданылмайды!",
                ex("If it rains, we will stay at home.", "Егер жаңбыр жауса, үйде қаламыз."),
                ex("If you study, you will pass the exam.", "Оқысаң, емтиханнан өтесің."),
            ),
            block(
                "Сөйлем бөліктерінің орны",
                "If бөлігі басында да, соңында да тұра алады. Басында тұрса, үтір қойылады.",
                ex("I will call you if I have time.", "Уақытым болса, саған қоңырау шаламын."),
            ),
            block(
                "unless — егер … болмаса",
                "unless = if … not.",
                ex("We will be late unless we hurry.", "Асықпасақ, кешігеміз."),
            ),
        ],
        "exercises": [
            choice(
                "If it ___ tomorrow, we will go to the park.",
                "Ертең күн ашық болса, саябаққа барамыз.",
                ["is sunny", "will be sunny", "was sunny"],
                "is sunny",
            ),
            choice("If you heat ice, it ___ .", "Мұзды қыздырсаң, ол ериді.", ["melts", "melted", "melting"], "melts"),
            choice("I ___ you if I see him.", "Оны көрсем, саған айтамын.", ["will tell", "tell", "told"], "will tell"),
            choice(
                "You will miss the bus ___ you leave now.",
                "Қазір шықпасаң, автобусқа үлгермейсің.",
                ["unless", "if", "when"],
                "unless",
            ),
            typed(
                "If I / have / money, I will buy a car",
                "Ақшам болса, көлік сатып аламын.",
                "If I have money, I will buy a car",
            ),
            typed(
                "If she / call, I / answer (future)", "Ол қоңырау шалса, жауап беремін.", "If she calls, I will answer"
            ),
        ],
        "words": [
            word("if", "егер, -са / -се", "If you are tired, rest.", "Шаршасаң, демал."),
            word("unless", "егер … болмаса", "Don't call unless it's important.", "Маңызды болмаса, қоңырау шалма."),
            word("otherwise", "әйтпесе", "Hurry, otherwise we will be late.", "Асық, әйтпесе кешігеміз."),
        ],
    },
    14: {
        "grammar_en": "common phrasal verbs (get up, wake up, look for, give up, turn on / off, put on, take off, "
        "find out, come back, go out, sit down, pick up, call back, look after)",
        "lesson": [
            block(
                "Етістік + шылау = жаңа мағына",
                "Фразалық етістік екі сөзден тұрады, мағынасы көбіне жаңа: look — қарау, look for — іздеу, "
                "look after — қамқорлық жасау. Оларды сөз ретінде тұтас жаттаған дұрыс.",
                ex("I am looking for my glasses.", "Көзілдірігімді іздеп жүрмін."),
                ex("She looks after her grandmother.", "Ол әжесіне қарайды."),
            ),
            block(
                "Шақтарда өзгеретін — етістік",
                "Шылау өзгермейді, етістік кесте бойынша өзгереді.",
                ex("I get up at seven. — I got up at seven.", "Жетіде тұрамын. — Жетіде тұрдым."),
                ex("Did you turn off the light?", "Жарықты өшірдің бе?"),
            ),
        ],
        "exercises": [
            choice(
                "I ___ at 6 a.m. every day.", "Күнде таңғы алтыда тұрамын.", ["get up", "get on", "give up"], "get up"
            ),
            choice(
                "Please ___ the TV. I want to sleep.",
                "Теледидарды өшірші, ұйықтағым келеді.",
                ["turn on", "turn off", "put on"],
                "turn off",
            ),
            choice("It's cold. ___ your coat.", "Суық. Пальтоңды ки.", ["Put on", "Take off", "Pick up"], "Put on"),
            choice(
                "I lost my keys. Can you help me ___ them?",
                "Кілтімді жоғалттым. Іздесуге көмектесесің бе?",
                ["look after", "look for", "find out"],
                "look for",
            ),
            choice(
                "Don't ___! You can do it.",
                "Берілме! Сен мұны істей аласың.",
                ["give up", "go out", "sit down"],
                "give up",
            ),
            typed("Past: she / come back / home", "Ол үйге қайтып келді.", "She came back home"),
        ],
        "words": [
            word("get up", "тұру (ұйқыдан)", "I get up early.", "Мен ерте тұрамын."),
            word("wake up", "ояну", "Wake up, it's eight!", "Оян, сағат сегіз болды!"),
            word("look for", "іздеу", "What are you looking for?", "Не іздеп жүрсің?"),
            word("look after", "қамқорлық жасау, қарау", "Who looks after your children?", "Балаларыңа кім қарайды?"),
            word("give up", "бас тарту, берілу", "He gave up smoking.", "Ол темекіні тастады."),
            word("turn on", "қосу", "Turn on the light, please.", "Жарықты қосшы."),
            word("turn off", "өшіру", "Turn off your phone.", "Телефоныңды өшір."),
            word("put on", "кию", "Put on your hat.", "Бас киіміңді ки."),
            word("take off", "шешу; ұшып көтерілу", "Take off your shoes.", "Аяқ киіміңді шеш."),
            word("find out", "білу, анықтау", "I found out the truth.", "Мен шындықты білдім."),
            word("come back", "қайтып келу", "When will you come back?", "Қашан қайтып келесің?"),
            word("go out", "сыртқа шығу; серуендеу", "Let's go out tonight.", "Бүгін кешке серуендеп қайтайық."),
            word("sit down", "отыру", "Please sit down.", "Отырыңыз."),
            word("pick up", "көтеру; алып кету", "I will pick you up at six.", "Сені алтыда алып кетемін."),
            word("call back", "қайта қоңырау шалу", "Can you call me back?", "Маған қайта қоңырау шала аласың ба?"),
        ],
    },
    15: {
        "grammar_en": "reported speech with the sequence of tenses (He said that he was busy)",
        "lesson": [
            block(
                "Төл сөз → төлеу сөз",
                "Біреудің сөзін жеткізгенде (said that…) шақ бір саты артқа ығысады: am / is → was, "
                "do / does → did, will → would.",
                ex('"I am busy." → She said that she was busy.', "«Бос емеспін» → Ол бос емес екенін айтты."),
                ex(
                    '"I will call you." → He said that he would call me.',
                    "«Қоңырау шаламын» → Ол маған қоңырау шалатынын айтты.",
                ),
            ),
            block(
                "Есімдіктер де өзгереді",
                "I → he / she, my → his / her, you → I (кім айтып тұрғанына қарай).",
                ex('"I like my job." → Asel said that she liked her job.', "Әсел өз жұмысын ұнататынын айтты."),
            ),
        ],
        "exercises": [
            choice(
                '"I am tired." → He said that he ___ tired.', "Ол шаршағанын айтты.", ["is", "was", "will be"], "was"
            ),
            choice(
                '"I will help." → She said that she ___ help.',
                "Ол көмектесетінін айтты.",
                ["will", "would", "can"],
                "would",
            ),
            choice(
                '"I like tea." → He said that he ___ tea.',
                "Ол шай ұнататынын айтты.",
                ["likes", "liked", "like"],
                "liked",
            ),
            choice(
                '"My car is new." → Dana said that ___ car was new.',
                "Дана көлігі жаңа екенін айтты.",
                ["my", "her", "his"],
                "her",
            ),
            typed(
                '"I live in Almaty." → She said that …',
                "Ол Алматыда тұратынын айтты.",
                "She said that she lived in Almaty",
                "She said she lived in Almaty",
            ),
        ],
        "words": [],
    },
    16: {
        "grammar_en": "free conversation using all the structures of the course",
        "lesson": [
            block(
                "Барлығын бірге қолдану",
                "Енді курстағы барлық құрылымдарды сөйлеуде қолдана аласыз. Ең жақсы жаттығу — AI-чаттағы "
                "«Еркін» режимі: өзіңіз туралы, жұмысыңыз, жоспарларыңыз туралы айтыңыз.",
                ex("I have lived in Almaty for five years.", "Алматыда бес жыл тұрып келемін."),
                ex(
                    "If I have time this weekend, I will visit my parents.",
                    "Демалыста уақытым болса, ата-анама барамын.",
                ),
                ex(
                    "Yesterday I was working when my friend called.",
                    "Кеше жұмыс істеп отырғанымда, досым қоңырау шалды.",
                ),
            ),
        ],
        "exercises": [
            choice(
                "I ___ English for two years.",
                "Екі жыл бойы ағылшын тілін оқып келемін.",
                ["study", "have studied", "studied"],
                "have studied",
            ),
            choice(
                "___ do you usually get up?", "Әдетте қашан тұрасың?", ["What time", "How many", "Whose"], "What time"
            ),
            choice(
                "She ___ cooking when I came.", "Мен келгенде ол тамақ дайындап жатқан.", ["was", "is", "did"], "was"
            ),
            choice(
                "This is ___ film I have ever seen.",
                "Бұл мен көрген ең жақсы фильм.",
                ["the best", "better", "good"],
                "the best",
            ),
            choice("If you ___ late, call me.", "Кешіксең, қоңырау шал.", ["are", "will be", "were"], "are"),
            choice(
                "You ___ wear a coat. It's cold.", "Пальто кигенің жөн. Суық.", ["should", "may", "would"], "should"
            ),
            typed("Past: we / meet / on Friday", "Біз жұма күні кездестік.", "We met on Friday"),
            typed("She can't / swim", "Ол жүзе алмайды.", "She can't swim", "She cannot swim"),
        ],
        "words": [],
    },
}


def apply(CourseStep, Vocabulary):
    """Writes the content into the database. Words keep their IPA from Wiktionary where they had one."""
    for number, content in STEPS.items():
        step = CourseStep.objects.get(number=number)
        step.lesson = content["lesson"]
        step.exercises = content["exercises"]
        step.grammar_en = content["grammar_en"]
        if content.get("description_kk"):
            step.description_kk = content["description_kk"]
        step.is_open = True
        step.save()
        for rank, (w, kk, past, example_en, example_kk, is_verb) in enumerate(content["words"], start=1):
            Vocabulary.objects.update_or_create(
                word=w,
                defaults={
                    "translation_kk": kk,
                    "past_form": past,
                    "is_irregular": bool(past),
                    "is_verb": is_verb,
                    "example_en": example_en,
                    "example_kk": example_kk,
                    "topic": f"step{number}",
                    "course_step": step,
                    "frequency_rank": number * 100 + rank,
                    "source": "course",
                },
            )
