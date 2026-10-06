# Unit JSON schema (content/book{N}.json)

```jsonc
{
  "book": 1,                       // Reading Juice for Kids level
  "units": [{
    "unit": 1,
    "title": "Elephant Families",
    "subject": "Science",            // or "Social Studies"
    "book_page": 6,                  // printed page number of the unit's first page
    "pdf_page": 7,                   // PDF page index (1-based) of the unit's first page
    "callouts": ["trunk", "grab"],   // handwritten labels on the photos (hero + passage page)
    "get_ready": {
      "q1": {
        "prompt": "What do elephants have?",
        "layout": "Plain description of the activity: 4 blank boxes before 'ears', 'legs', 'trunks', 'skin'; word bank below.",
        "word_bank": ["long", "strong", "gray", "big"],
        "items": [ {"text": "___ ears", "answers": ["big"]} ],   // one entry per blank; answers = every word that is correct
        "open": true                // true when several answers are reasonable (opinion/prior knowledge)
      },
      "listen_words": ["learn", "carry", "caring", "spend", "trunk", "grab"]   // reading order: row by row, left→right
    },
    "passage": ["<paragraph 1 exactly as printed>", "<paragraph 2>"], // one string per paragraph, EXACT book text
    "comprehension": [
      {"n": 1, "type": "mc", "stem": "The passage is mainly about ___.", "options": ["elephant families", "elephant trunks"], "answer": 0, "pictures": false},
      {"n": 2, "type": "mc", "stem": "Elephants learn how to use their ___.", "options": ["ears", "trunk"], "answer": 1, "pictures": true, "picture_desc": ["elephant with ears circled", "elephant trunk"]},
      {"n": 4, "type": "tf", "stem": "Baby elephants learn to carry water.", "answer": true}
    ],
    "build_vocab": {
      "instruction": "Complete the sentences.",
      "word_bank": ["learn", "spend", "carry"],
      "items": [{"n": 1, "stem": "I am strong. I can ___ many books.", "answer": "carry"}]
    },
    "organizer": {
      "instruction": "Complete the graphic organizer.",
      "kind": "main idea + details",          // describe the diagram shape
      "rows": [
        {"label": "Main Idea", "text": "Elephants live in ___.", "answers": ["families"]},
        {"label": "Detail 1", "text": "___ teach their babies.", "answers": ["Mother elephants"]},
        {"label": "Detail 2", "text": "Elephant families spend time ___.", "answers": ["together"]}
      ],
      "word_bank": ["families", "their babies", "Mother elephants", "together"],
      "example": ["their babies"]           // word-bank entries already used as a printed example (shown underlined/colored)
    },
    "glossary": [{"word": "learn", "def": "to get new information or knowledge"}],
    "notes": []                              // anything uncertain, typos in the book, ambiguous keys
  }],
  "vocab_checks": [{
    "n": 1, "after_unit": 4, "book_page": 22, "pdf_page": 23,
    "sections": [
      {"instruction": "Match the pictures with the words.", "type": "picture_match",
       "options": ["trunk", "land", "submarine"],
       "items": [{"n": 1, "picture_desc": "elephant trunk", "answer": "trunk"}]},
      {"instruction": "Match the words with the similar meanings.", "type": "match",
       "options": ["well-known", "many", "give birth"],
       "items": [{"n": 1, "stem": "a lot of", "answer": "many"}]},
      {"instruction": "Choose the correct answers.", "type": "mc",
       "items": [{"n": 1, "stem": "Frogs swim in the ___.", "options": ["sea", "ponds"], "answer": 1}]},
      {"instruction": "Complete the dialogue.", "type": "cloze", "word_bank": ["hunt", "feed", "busy"],
       "text": "A: How do lions take care of their babies?\nB: Lions wash their babies and play with them. They are very [1].\nA: How do lions [2] their babies?\nB: They [3] other small animals for their babies.",
       "answers": {"1": "busy", "2": "feed", "3": "hunt"}}
    ],
    "notes": []
  }]
}
```

Rules
- Blanks are written as `___` (three underscores) in stems; in cloze `text` use `[1]`, `[2]` ….
- `answer` for `mc` is the 0-based option index (a=0, b=1, c=2 …). `tf` answer is a boolean.
- Answers come from the passage. The book has no answer key, so each answer must be provable from the passage text or the glossary; put any doubt in `notes`.
- Keep the book's spelling, capitalisation and punctuation. Use straight quotes `'` and `"`. No hyphenation artefacts.
