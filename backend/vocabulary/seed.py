"""Starter content: the 16-step course map and the 40 verbs of step 1 (SRS-08).

Our own wording and examples. Kazakh texts must be checked by a native speaker before launch.
"""

COURSE_STEPS = [
    (1, "Негізгі кесте", "Basic verb table", "Үш шақ × сұрақ, болымды, болымсыз. 40 жиі етістік.", True),
    (2, "Сұраулы сөздер", "Question words", "what, where, when, why, who, how", False),
    (3, "to be етістігі", "The verb to be", "am, is, are, was, were", False),
    (4, "Предлогтар", "Prepositions", "in, on, at, to, from", False),
    (5, "Тәуелдік есімдіктер", "Possessive pronouns", "my, your, his, her, our, their", False),
    (6, "Бұрыс етістіктер", "Irregular verbs", "Жиі қолданылатын 60 бұрыс етістік", False),
    (7, "Модаль етістіктер", "Modal verbs", "can, must, should, may", False),
    (8, "Созылыңқы шақтар", "Continuous", "I am working, I was working", False),
    (9, "Present Perfect", "Present Perfect", "I have done", False),
    (10, "Сын есім шырайлары", "Degrees of comparison", "big, bigger, the biggest", False),
    (11, "Сандар мен күндер", "Numbers and dates", "Сандар, уақыт, күн мен ай", False),
    (12, "Ырықсыз етіс", "Passive voice", "It was made in Kazakhstan", False),
    (13, "Шартты сөйлемдер", "Conditionals", "If I have time, I will call you", False),
    (14, "Фразалық етістіктер", "Phrasal verbs", "get up, look for, give up", False),
    (15, "Шақтардың сәйкестігі", "Sequence of tenses", "She said that she was busy", False),
    (16, "Еркін сөйлеу", "Free speech", "Барлық құрылымдарды сөйлеуде қолдану", False),
]

# word, translation_kk, ipa, past_form (irregular only), example_en, example_kk
VERBS = [
    ("have", "ие болу, бар болу", "/hæv/", "had", "I have a car.", "Менің көлігім бар."),
    ("do", "істеу, орындау", "/duː/", "did", "I do my homework every day.", "Мен үй тапсырмасын күнде орындаймын."),
    ("say", "айту", "/seɪ/", "said", "She says hello.", "Ол сәлем айтады."),
    ("go", "бару", "/ɡəʊ/", "went", "We go to work by bus.", "Біз жұмысқа автобуспен барамыз."),
    ("get", "алу", "/ɡet/", "got", "I get a lot of emails.", "Мен көп хат аламын."),
    ("make", "жасау", "/meɪk/", "made", "She makes tea in the morning.", "Ол таңертең шай демдейді."),
    ("know", "білу", "/nəʊ/", "knew", "I know the answer.", "Мен жауапты білемін."),
    ("think", "ойлау", "/θɪŋk/", "thought", "I think about my family.", "Мен отбасым туралы ойлаймын."),
    ("take", "алу, алып кету", "/teɪk/", "took", "He takes the book.", "Ол кітапты алады."),
    ("see", "көру", "/siː/", "saw", "I see my friends on Sunday.", "Мен достарымды жексенбіде көремін."),
    ("come", "келу", "/kʌm/", "came", "They come home at six.", "Олар үйге сағат алтыда келеді."),
    ("want", "қалау", "/wɒnt/", "", "I want a cup of coffee.", "Мен бір кесе кофе ішкім келеді."),
    ("look", "қарау", "/lʊk/", "", "She looks at the photo.", "Ол суретке қарайды."),
    ("use", "пайдалану", "/juːz/", "", "We use English at work.", "Біз жұмыста ағылшын тілін пайдаланамыз."),
    ("find", "табу", "/faɪnd/", "found", "I found my keys.", "Мен кілттерімді таптым."),
    ("give", "беру", "/ɡɪv/", "gave", "He gives me a book.", "Ол маған кітап береді."),
    ("tell", "айтып беру", "/tel/", "told", "She told me the news.", "Ол маған жаңалықты айтты."),
    ("work", "жұмыс істеу", "/wɜːk/", "", "I work in a bank.", "Мен банкте жұмыс істеймін."),
    ("call", "қоңырау шалу", "/kɔːl/", "", "I call my mother every evening.", "Мен анама күнде кешке қоңырау шаламын."),
    ("try", "тырысу", "/traɪ/", "", "I try to speak English.", "Мен ағылшынша сөйлеуге тырысамын."),
    ("ask", "сұрау", "/ɑːsk/", "", "The teacher asks a question.", "Мұғалім сұрақ қояды."),
    ("need", "керек болу", "/niːd/", "", "I need help.", "Маған көмек керек."),
    ("study", "оқу, зерттеу", "/ˈstʌdi/", "", "She studies English.", "Ол ағылшын тілін оқиды."),
    ("leave", "кету, шығу", "/liːv/", "left", "We leave home at eight.", "Біз үйден сағат сегізде шығамыз."),
    ("live", "тұру, өмір сүру", "/lɪv/", "", "They live in Almaty.", "Олар Алматыда тұрады."),
    ("love", "жақсы көру", "/lʌv/", "", "I love my city.", "Мен өз қаламды жақсы көремін."),
    ("like", "ұнату", "/laɪk/", "", "He likes football.", "Ол футболды ұнатады."),
    ("help", "көмектесу", "/help/", "", "My friends help me.", "Достарым маған көмектеседі."),
    ("start", "бастау", "/stɑːt/", "", "We start work at nine.", "Біз жұмысты сағат тоғызда бастаймыз."),
    ("play", "ойнау", "/pleɪ/", "", "Children play in the park.", "Балалар саябақта ойнайды."),
    ("buy", "сатып алу", "/baɪ/", "bought", "She bought a new phone.", "Ол жаңа телефон сатып алды."),
    ("speak", "сөйлеу", "/spiːk/", "spoke", "I speak Kazakh and English.", "Мен қазақша және ағылшынша сөйлеймін."),
    ("read", "оқу", "/riːd/", "read", "I read a book every evening.", "Мен күнде кешке кітап оқимын."),
    ("write", "жазу", "/raɪt/", "wrote", "He writes a letter.", "Ол хат жазады."),
    ("open", "ашу", "/ˈəʊpən/", "", "She opens the window.", "Ол терезені ашады."),
    ("close", "жабу", "/kləʊz/", "", "They close the shop at ten.", "Олар дүкенді сағат онда жабады."),
    ("eat", "жеу", "/iːt/", "ate", "We eat lunch at one.", "Біз сағат бірде түскі ас ішеміз."),
    ("drink", "ішу", "/drɪŋk/", "drank", "I drink tea with milk.", "Мен сүт қосылған шай ішемін."),
    ("learn", "үйрену", "/lɜːn/", "", "We learn new words.", "Біз жаңа сөздер үйренеміз."),
    ("watch", "көру, тамашалау", "/wɒtʃ/", "", "They watch TV in the evening.", "Олар кешке теледидар көреді."),
]


def seed(CourseStep, Vocabulary):
    steps = {}
    for number, title_kk, title_en, description_kk, is_open in COURSE_STEPS:
        steps[number], _ = CourseStep.objects.update_or_create(
            number=number,
            defaults={"title_kk": title_kk, "title_en": title_en, "description_kk": description_kk, "is_open": is_open},
        )
    for rank, (word, kk, ipa, past, ex_en, ex_kk) in enumerate(VERBS, start=1):
        Vocabulary.objects.update_or_create(
            word=word,
            defaults={
                "translation_kk": kk,
                "ipa": ipa,
                "past_form": past,
                "is_irregular": bool(past),
                "example_en": ex_en,
                "example_kk": ex_kk,
                "topic": "verbs",
                "course_step": steps[1],
                "frequency_rank": rank,
                "is_verb": True,
            },
        )
