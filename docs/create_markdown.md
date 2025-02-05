4. 実装のタスク分解
A. FastAPI エンドポイント実装
エンドポイント定義
app/src/endpoints/fortune.py に /fortuneなどのエンドポイントを作成。
リクエストボディ(ClientInput)を受け取る POST メソッドを用意する。
受け取った browsing_history が空かどうかをチェックし、空であれば create_topics をスキップし、あらかじめ用意した default_topics を使うようにする。
（browsing_history が空でなければ従来通り create_topics を呼び出す）
ビジネスロジック呼び出し
リクエストボディをもとに services 下の関数を順次コール。
B. 閲覧履歴データ取得 & ロジックサーバーデータ取得
閲覧履歴データ
ClientInputのbrowsing_historyを閲覧履歴データとして読み込む
Mock用リポジトリ
app/src/repository/mock_repository.py を作り、ファイル(app/tests/mockdata/)から ロジックサーバーデータ(logic_data.xml) を読み込む。
実際の外部API取得用リポジトリ(将来的)
app/src/repository/external_repository.py などを作り、外部サーバー（ロジックサーバー）から同様のデータを取得する処理を実装。
ロジックサーバーのアクセス方法はdocs/how_to_access_logic_server.md を参照。
設定ファイル or 環境変数で切り替え
app/config/settings.py 内で USE_MOCK = True/False 等を管理し、リポジトリを切り替える。
C. create_topics (LLM呼出)
サービス層 (create_topics_service.py)
※ 閲覧履歴 (browsing_history) が空の場合はこのステップをスキップし、デフォルトのトピックデータを使用する。スキップ時には LLM 呼び出しも行わない
閲覧履歴データはClientInputのbrowsing_historyを参照する
create_topics_prompt(app/src/prompt/create_topics_prompts.py)を呼び出し、{browsing_history}を埋め込んで LLM(Claudeなど) へリクエスト。
返却された JSON をパースし、FortuneItems(Pydantic)としてバリデーションする（6件のタイトルがあるか）。
出力: FortuneItems
LLM実装方法
docs/how_to_use_bedrock_claude.md を参照。
実際のAPI呼び出し部分は utils/llm_client.py などにまとめるイメージでもOK。
D. XMLパース (parse_logic_data_service.py)
サービス層
ロジックサーバーから取得したデータを読み込み、以下の条件を満たすLogicDataを作る
personalityの抽出
<title>1</title>を含む<content>ブロックを探す
その中の<explanation id="text1">の内容をpersonalityとして抽出する
守護霊データ(ghost_data)の抽出
<explanation id="ghost">を含む<content>ブロックを探す
各ブロックから以下の情報を取得
キー: <explanation id="ghost">の値
 値: 同じ<content>内の<explanation id="text1">の内容
同じ守護霊IDの場合はテキストを結合する
守護霊ID(ghost_ids)の抽出
全ての<explanation id="ghost">の値を配列として収集
重複を排除して配列に格納
昇順にソート
logic_data.xml を読み込み、以下の要件を満たす LogicData を作る。
personality: <title>1</title>と<explanation id='menu'> を含む <content> の <text1> のみ。
ghost_data: <explanation id='ghost'> を含む <content> の<text1>で、ghost_id ごとに <text1> を配列で集め、重複を除去して join。
ghost_ids: 上記で取得できた ghost_id のユニークリスト（1〜5）。
バリデーション
Pydanticの LogicData を使って不正がないかチェック。
E. fortune_items 分割 → FortuneBlock
入力データ
FortuneItems
items配列に6件のFortuneItemを保持
LogicData
ghost_idsの配列に守護霊IDを保持
分割ルール
ghost_idのユニーク数 n (1~4) に応じて 6件のfortune_itemsを分割:
n=1 : [1,2,3,4,5,6] → 1つのブロック
n=2 : [1,2,3], [4,5,6] → 2つのブロック
n=3 : [1,2], [3,4], [5,6] → 3つのブロック
n=4 : [1], [2], [3,4], [5,6] → 4つのブロック
生成方法
LogicDataのghost_idsの要素数を取得
要素数に応じた分割パターンを決定
FortuneItemsのitems配列を分割パターンに従って分割
各分割グループに対して
ghost_id:ghost_idsの対応する値を設定
fortune_titles:分割されたタイトル群を設定
FortuneBlock の ghost_id (1個目のブロック = ghost_ids[0], 2個目 = ghost_ids[1], ...と対応)
fortune_titles に分割された FortuneItem の配列を入れる。
F. ghost_tone_model (LLM呼出)
口調別アドバイス生成
分割したブロック(FortuneBlock)の配列の各要素に対して、以下の処理を行う
app/src/prompts/ghost_tone_prompts.py内からプロンプトを選択する
ghost_id=1:商人
ghost_id=2:頑固親父
ghost_id=3:おばあ
ghost_id=4:花魁
ghost_id=5:猫
system_prompt、user_promptにFortuneBlockのghost_idに等しい下記のデータを埋め込む
{titles}: FortuneBlockのfortune_titlesの配列
{personality}: LogicDataのpersonality
{ghost_data}: LogicDataのghost_data
LLMによるトークン生成を行う
生成されたトークンをGhostToneOutputItemのスキーマに従って配列に格納する


分割したブロック(ghost_id=1,2,3...)を順に、対応する app/src/promot/ghost_tone_prompts.py 内の system_prompt / user_prompt に差し込む。閲覧履歴が空のときは app/src/prompts/ghost_tone_nohistory_prompts.pyに差し込む
{title}は各ghost_idに等しいfortune_titles(FotuneBlock)を参照。
{reference}はLogicDataのghost_dataのkeyがghost_idに等しいデータを参照
{titles}, {reference}, {personality} などを埋め込んで LLM へ依頼。
出力形式
LLMからの出力はJSONの配列で [{"ghost_id": 1, "title": "xxx", "content": "yyy"}, ...] の形式を期待。
これをパースし、GhostToneOutputItem の配列で受け取る。
G. summary_model (LLM呼出)
入力データ
GhostToneOutputItemの配列が入力
各アイテムは以下の要素を含む
ghost_id:守護霊のID
title:タイトル
content:本文内容
処理手順
入力データの各アイテムに対して以下の処理を実行
app/src/prompts/summary_prompts.pyからプロンプトを取得
system_prompt、user_promptに入力データを埋め込み
LLM は、各アイテムの要約結果を SummarizedGhostToneOutputItem スキーマとして JSON 形式で返す
生成されたトークンをSummaryResultのスキーマに従って配列に格納する
各アイテムをSummaryResult形式に変換
ghost_idは元のghost_idを維持
summaryは20文字以内に要約した文字列
contentは元のcontentの全文
20文字要約
ghost_tone_model で得られた各要素の content を、summary_prompts.py に定義したプロンプトで呼び出し、20文字以内に要約する。
出力格納
まとめて SummaryResult の配列に変換し、ghost_id, summary, content を持たせる。
H. 最終結果まとめ
出力形式
出力スキーマはClientOutputとし、BODYにこれを指定する
resultsは必ず1つ以上のSummaryResultが格納されています。
レスポンス例は下記に提示します。

レスポンス例
json
コピーする
{
  "results": [
    {
      "ghost_id": 1,
      "summary": "●●(20文字以内)",
      "content": "要約元の長いアドバイス"
    },
    {
      "ghost_id": 2,
      "summary": "・・・",
      "content": "・・・"
    },
    ...
  ]
}


バリデーション
まとめたオブジェクトを Pydanticモデル（必要に応じて作成）経由で返却。

データサンプル
APIの入力サンプル

{
  "datetime": "2025-01-23",
  "birthday": "1999-01-01",
  "browsing_history": [
    {
      "category": "誕生日が分からないあの人との恋",
      "title": "友達だけど、少しでも異性を意識してくれてる？"
    },
    {
      "category": "",
      "title": "家編"
    },
    {
      "category": "あなたの恋の出会い",
      "title": "私に魅力を感じてくれる人はいる？"
    }
  ]
}

トピックデータ(FortuneItems)のサンプル

{
  "items": [
    {"title": "あなたの隠れた魅力と、それを活かす最適なタイミング"},
    {"title": "今後半年間であなたの人間関係が好転するきっかけ"},
    {"title": "あなたの金運を上げる秘訣と、意外な才能の開花時期"},
    {"title": "周囲があなたを必要としている意外な理由"},
    {"title": "ストレスを味方につける方法と、転機となる出来事"},
    {"title": "あなたの人生が大きく変わる、重要な決断のとき"}
  ]
}

ロジックサーバの出力サンプル

<?xml version="1.0" encoding="Windows-31J" ?>
<uranai>
  <content>
    <title>0</title>
    <explanation id = 'num'>4</explanation>
  </content>
  <content>
    <title>1</title>
    <explanation id = 'menu'>2002</explanation>
    <explanation id = 'id'>13</explanation>
    <explanation id = 'text1'>本当に繊細な人なんだね。だから迷っちゃうコトもあるし、人を気遣うコトもできるんだよ。本心から、｢世の中が平和でいてほしい。誰も傷ついてほしくない｣って思ってるんじゃない？ただ、そういう気持ちを、わざわざ誰かに主張するコトもないんだろうね。自分の考えを伝えるコトで、誰かの気分を害したらいけないって考えるんだよ。でもね、あんまり迷わなくってもいいみたい。あなた自身が｢ちょっと大胆な決断かな｣って思ったコトでも、実はものすごくいろいろ考えた末の決断になっているはずだからさ。傷ついたらどうしようって不安になるかもしれないケド、大丈夫!!どんなコトだって乗り越えて強さに変えていけるのも、あなたらしい純粋さなんだよ。</explanation>
  </content>
  <content>
    <title>04.守護霊ID[1]x運気ID[2](N:太陽/T:太陽/60度)</title>
    <explanation id = 'menu'>1</explanation>
    <explanation id = 'id'>2</explanation>
    <explanation id = 'text1'>注目が集まる。実力が出せる。身の丈に合った行動。主役になりやすい。何か主張をするのに良い時。成果を出せる。やりすぎ注意。</explanation>
    <explanation id = 'ghost'>1</explanation>
  </content>
  <content>
    <title>17.守護霊ID[2]x運気ID[6](N:太陽/T:火星/180度)</title>
    <explanation id = 'menu'>1</explanation>
    <explanation id = 'id'>6</explanation>
    <explanation id = 'text1'>恋愛に緊張感がある。トラウマとの対決。苦い恋。親が反対する恋。その恋愛を通して何かを学ぶようなこと。</explanation>
    <explanation id = 'ghost'>2</explanation>
  </content>
  <content>
    <title>26.守護霊ID[4]x運気ID[9](N:金星/T:火星/180度)</title>
    <explanation id = 'menu'>1</explanation>
    <explanation id = 'id'>9</explanation>
    <explanation id = 'text1'>良くも悪くも恋愛や趣味にスポットがあたる。恋の主役になる。悪い男も引き寄せる。自分の恋の理想、こだわりが強くなりすぎてしまう危険。</explanation>
    <explanation id = 'ghost'>4</explanation>
  </content>
  <content>
    <title>28.守護霊ID[4]x運気ID[10](N:金星/T:金星/60度)</title>
    <explanation id = 'menu'>1</explanation>
    <explanation id = 'id'>10</explanation>
    <explanation id = 'text1'>恋愛モードになる。楽しいことがやってくる。収入の見直し。自分への投資。自分磨き。身近なところでのモテ期。誠実な出会い。</explanation>
    <explanation id = 'ghost'>4</explanation>
  </content>
  <result>2000</result>
</uranai>


LogicDataのサンプル

{
  "personality": "本当に繊細な人なんだね。だから迷っちゃうコトもあるし、人を気遣うコトもできるんだよ。本心から、｢世の中が平和でいてほしい。誰も傷ついてほしくない｣って思ってるんじゃない？ただ、そういう気持ちを、わざわざ誰かに主張するコトもないんだろうね。自分の考えを伝えるコトで、誰かの気分を害したらいけないって考えるんだよ。でもね、あんまり迷わなくってもいいみたい。あなた自身が｢ちょっと大胆な決断かな｣って思ったコトでも、実はものすごくいろいろ考えた末の決断になっているはずだからさ。傷ついたらどうしようって不安になるかもしれないケド、大丈夫!!どんなコトだって乗り越えて強さに変えていけるのも、あなたらしい純粋さなんだよ。<
  ",
  "ghost_data": {
    "1": "注目が集まる。実力が出せる。身の丈に合った行動。主役になりやすい。何か主張をするのに良い時。成果を出せる。やりすぎ注意。",
    "2": "恋愛に緊張感がある。トラウマとの対決。苦い恋。親が反対する恋。その恋愛を通して何かを学ぶようなこと。",
    "4": "良くも悪くも恋愛や趣味にスポットがあたる。恋の主役になる。悪い男も引き寄せる。自分の恋の理想、こだわりが強くなりすぎてしまう危険。恋愛モードになる。楽しいことがやってくる。収入の見直し。自分への投資。自分磨き。身近なところでのモテ期。誠実な出会い。",
  },
  "ghost_ids": [1, 2, 4]
}

FortuneBlockの配列

[
  {
    "ghost_id": 1,
    "fortune_titles": [
      {"title": "あなたの隠れた魅力と、それを活かす最適なタイミング"},
      {"title": "今後半年間であなたの人間関係が好転するきっかけ"}
    ]
  },
  {
    "ghost_id": 2,
    "fortune_titles": [
      {"title": "あなたの金運を上げる秘訣と、意外な才能の開花時期"},
      {"title": "周囲があなたを必要としている意外な理由"}
    ]
  },
  {
    "ghost_id": 4,
    "fortune_titles": [
      {"title": "ストレスを味方につける方法と、転機となる出来事"},
      {"title": "あなたの人生が大きく変わる、重要な決断のとき"}
    ]
  }
]

LLMに埋め込むデータのサンプル
商人(ghost_id=1)

{
  "titles": [
    {"title": "あなたの隠れた魅力と、それを活かす最適なタイミング"},
    {"title": "今後半年間であなたの人間関係が好転するきっかけ"}
  ],
  "personality": "本当に繊細な人なんだね。だから迷っちゃうコトもあるし、人を気遣うコトもできるんだよ。本心から、｢世の中が平和でいてほしい。誰も傷ついてほしくない｣って思ってるんじゃない？ただ、そういう気持ちを、わざわざ誰かに主張するコトもないんだろうね。自分の考えを伝えるコトで、誰かの気分を害したらいけないって考えるんだよ。でもね、あんまり迷わなくってもいいみたい。あなた自身が｢ちょっと大胆な決断かな｣って思ったコトでも、実はものすごくいろいろ考えた末の決断になっているはずだからさ。傷ついたらどうしようって不安になるかもしれないケド、大丈夫!!どんなコトだって乗り越えて強さに変えていけるのも、あなたらしい純粋さなんだよ。",
  "reference": "注目が集まる。実力が出せる。身の丈に合った行動。主役になりやすい。何か主張をするのに良い時。成果を出せる。やりすぎ注意。"
}
頑固親父(ghost_id=2)

{
  "titles": [
    {"title": "あなたの金運を上げる秘訣と、意外な才能の開花時期"},
    {"title": "周囲があなたを必要としている意外な理由"}
  ],
  "personality": "本当に繊細な人なんだね。[前述の全文]",
  "reference": "恋愛に緊張感がある。トラウマとの対決。苦い恋。親が反対する恋。その恋愛を通して何かを学ぶようなこと。"
}

花魁(ghost_id=4)

{
  "titles": [
    {"title": "ストレスを味方につける方法と、転機となる出来事"},
    {"title": "あなたの人生が大きく変わる、重要な決断のとき"}
  ],
  "personality": "本当に繊細な人なんだね。[前述の全文]",
  "reference": "良くも悪くも恋愛や趣味にスポットがあたる。恋の主役になる。悪い男も引き寄せる。自分の恋の理想、こだわりが強くなりすぎてしまう危険。恋愛モードになる。楽しいことがやってくる。収入の見直し。自分への投資。自分磨き。身近なところでのモテ期。誠実な出会い。"
}


GhostToneOutputItemの出力例
商人(ghost_id=1)

{
  "items": [
    {
      "ghost_id": 1,
      "title": "あなたの隠れた魅力と、それを活かす最適なタイミング",
      "content": "おいおい、今のおまえさんには人の注目を集める力が宿っているんだぜ。実力を発揮できる好機が巡ってきてるってわけよ。だがな、やりすぎは禁物だ。身の丈に合った行動を心がけるんだ。主役になれる運が巡ってきてるから、自分の考えをしっかり伝えていくといいぜ。ただし、成果を焦るのは禁物だな。"
    },
    {
      "ghost_id": 1,
      "title": "今後半年間であなたの人間関係が好転するきっかけ",
      "content": "あたしから言わせてもらうとよ、今は自分の意見をはっきり言える運が巡ってきてるんだ。周りの人に対して、遠慮せずに自分の考えを伝えていくといいぜ。ただしな、相手の立場も考えながら、身の丈に合った発言を心がけるんだ。そうすりゃ、周りもおまえさんの本質を理解してくれて、関係が深まっていくってわけよ。"
    }
  ]
}
頑固親父(ghost_id=2)

{
  "items": [
    {
      "ghost_id": 2,
      "title": "あなたの金運を上げる秘訣と、意外な才能の開花時期",
      "content": "おう、今のおめえには試練が巡ってきてるんだ。恋愛でも何かと緊張する出来事が続くかもしれねえが、そこから学びを得られる運が巡ってきてるんだぞ。親に反対されるような道でも、そこから得られる教訓があるってことだ。この苦労を乗り越えた先に、おめえの才能が開花する好機が待ってるんだ。おめえならできる！"
    },
    {
      "ghost_id": 2,
      "title": "周囲があなたを必要としている意外な理由",
      "content": "よく聞けよ。今のおめえには、困難に立ち向かう運が巡ってきてるんだ。その姿を見て、周りの連中が勇気づけられてるってわけよ。トラウマと向き合う覚悟を持てる人間は、周りにとっても大切な存在なんだぞ。だからこそ、おめえの行動一つ一つが、周りの道標になってるってことをしっかり覚えておけ。"
    }
  ]
}

花魁(ghost_id=4)

{
  "items": [
    {
      "ghost_id": 4,
      "title": "ストレスを味方につける方法と、転機となる出来事",
      "content": "あら、聞いておくれよ！今のあんたには恋愛や趣味で注目を集める運が巡ってきてるのよ。でもね、自分の理想にこだわりすぎると、かえって良い出会いを逃してしまうかもしれないわ。ストレスを感じたら、それを自分磨きのきっかけに変えてごらんなさい。今は収入の見直しや自分への投資が実を結ぶ時なのよ。"
    },
    {
      "ghost_id": 4,
      "title": "あなたの人生が大きく変わる、重要な決断のとき",
      "content": "これは大事なことだから、よく聞いておくれ！今のあんたには、誠実な出会いが訪れる運気が宿ってるわ。でも、悪い縁も引き寄せやすい時でもあるの。だからこそ、出会いを選り好みするんじゃなく、身近な人との縁を大切にしていきなさいな。楽しい出来事が待ってるから、あまり深刻に考えすぎないことね。"
    }
  ]
}


SummarizedGhostToneOutputItemサンプル

[
  {
    "ghost_id": 1,
    "item_index": 0,
    "summary": "おまえさんの魅力が輝くぜ！焦らず前に進もう"
  },
  {
    "ghost_id": 1,
    "item_index": 1,
    "summary": "遠慮せずに自分の意見を伝えていこうぜ！"
  },
  {
    "ghost_id": 2,
    "item_index": 0,
    "summary": "試練を乗り越えろ！その先に才能開花が待ってるぞ"
  },
  {
    "ghost_id": 2,
    "item_index": 1,
    "summary": "おめえの行動が周りの道標になってるんだぞ！"
  },
  {
    "ghost_id": 4,
    "item_index": 0,
    "summary": "あなたの魅力が開花するわよ！ストレスも味方につけて"
  },
  {
    "ghost_id": 4,
    "item_index": 1,
    "summary": "誠実な出会いが待ってるわ！身近な縁を大切にして"
  }
]

ClientOutputサンプル(SummaryResultの配列)

{
  "results": [
    {
      "ghost_id": 1,
      "summary": "チャンスを活かせ！",
      "content": "おいおい、今のおまえさんには人の注目を集める力が宿っているんだぜ。実力を発揮できる好機が巡ってきてるってわけよ。だがな、やりすぎは禁物だ。身の丈に合った行動を心がけるんだ。主役になれる運が巡ってきてるから、自分の考えをしっかり伝えていくといいぜ。ただし、成果を焦るのは禁物だな。"
    },
    {
      "ghost_id": 1,
      "summary": "遠慮せず意見を！",
      "content": "あたしから言わせてもらうとよ、今は自分の意見をはっきり言える運が巡ってきてるんだ。周りの人に対して、遠慮せずに自分の考えを伝えていくといいぜ。ただしな、相手の立場も考えながら、身の丈に合った発言を心がけるんだ。そうすりゃ、周りもおまえさんの本質を理解してくれて、関係が深まっていくってわけよ。"
    },
    {
      "ghost_id": 2,
      "summary": "試練を乗り越えろ！",
      "content": "おう、今のおめえには試練が巡ってきてるんだ。恋愛でも何かと緊張する出来事が続くかもしれねえが、そこから学びを得られる運が巡ってきてるんだぞ。親に反対されるような道でも、そこから得られる教訓があるってことだ。この苦労を乗り越えた先に、おめえの才能が開花する好機が待ってるんだ。おめえならできる！"
    },
    {
      "ghost_id": 2,
      "summary": "君の姿が道標だ！",
      "content": "よく聞けよ。今のおめえには、困難に立ち向かう運が巡ってきてるんだ。その姿を見て、周りの連中が勇気づけられてるってわけよ。トラウマと向き合う覚悟を持てる人間は、周りにとっても大切な存在なんだぞ。だからこそ、おめえの行動一つ一つが、周りの道標になってるってことをしっかり覚えておけ。"
    },
    {
      "ghost_id": 4,
      "summary": "注目の的よ！",
      "content": "あら、聞いておくれよ！今のあんたには恋愛や趣味で注目を集める運が巡ってきてるのよ。でもね、自分の理想にこだわりすぎると、かえって良い出会いを逃してしまうかもしれないわ。ストレスを感じたら、それを自分磨きのきっかけに変えてごらんなさい。今は収入の見直しや自分への投資が実を結ぶ時なのよ。"
    },
    {
      "ghost_id": 4,
      "summary": "縁を大切にして！",
      "content": "これは大事なことだから、よく聞いておくれ！今のあんたには、誠実な出会いが訪れる運気が宿ってるわ。でも、悪い縁も引き寄せやすい時でもあるの。だからこそ、出会いを選り好みするんじゃなく、身近な人との縁を大切にしていきなさいな。楽しい出来事が待ってるから、あまり深刻に考えすぎないことね。"
    }
  ]
}


プロジェクトのルールに従って実装すること。
docが存在する場合は、その実装方法を優先して実装すること。


#プロジェクトのディレクトリ構成

```
.
├── .env                               # 環境変数ファイル（※通常.gitignore対象）※読み取り、編集禁止
├── app                                # アプリケーションのルートフォルダ
│   ├── src                            # ソースコード
│   │   ├── main.py                   # FastAPIエントリポイント
│   │   ├── endpoints                 # ルーティングやエンドポイントを定義
│   │   │   └── fortune.py            # /fortune 等のエンドポイント例
│   │   ├── services                  # ビジネスロジックやLLM呼出し処理などをまとめる
│   │   │   ├── create_topics_service.py       # create_topics用サービス
│   │   │   ├── parse_logic_data_service.py    # XMLをパースしてLogicDataを生成するサービス
│   │   │   ├── ghost_tone_service.py          # ghost_tone_model（LLM）呼び出し
│   │   │   ├── summary_service.py             # 内容を20文字以内で要約するサービス
│   │   │   └── fortune_block_service.py       # 分割処理など
│   │   ├── repository               # データ取得リポジトリ
│   │   │   ├── mock_repository.py   # mockdataからデータ取得するリポジトリ
│   │   │   └── external_repository.py  # 外部APIなど本番用のデータ取得リポジトリ(将来的に)
│   │   ├── models                   # DBモデルやORマッパーを使うならここに置く
│   │   ├── utils                    # 共通ユーティリティ
│   │   │   └── llm_client.py        # 実際にClaude API呼び出しなどを行う処理
│   │   ├── data                     # 閲覧履歴がない時のデフォルトのトピックのデータを格納
│   │   │   └── default_topics.py    # 閲覧履歴がない時に使用するデフォルトのトピック
│   │   ├── prompt                   # プロンプトファイルを格納
│   │   │   ├── create_topics_prompts.py       # create_topics用のPrompt
│   │   │   ├── ghost_tone_prompts.py          # ghost_tone用のPrompt
│   │   │   ├── ghost_tone_nohistory_prompts.py  # 閲覧履歴がない時に使うghost_tone用のPrompt
│   │   │   └── summary_prompts.py             # summary用のPrompt
│   │   ├── config                       # 設定関連
│   │   │   └── settings.py             # 設定値を管理する
│   │   ├── schema                       # Pydanticスキーマ
│   │   │   └── schema.py               # FortuneItem, LogicData, FortuneBlockなどの定義、※編集禁止
│   │   └── __init__.py              # Pythonパッケージとして認識させるためのファイル
│   ├── tests                        # テスト関連
│   │   ├── mockdata                 # テスト用のモックデータ
│   │   │   ├── client_input.json    # リクエストボディのモックデータ、※編集禁止
│   │   │   └── logic_data.xml       # テスト用のロジックデータ（XML）、※編集禁止
│   │   ├── test_endpoints           # エンドポイントのユニット/結合テスト
│   │   ├── test_services            # サービス層のユニットテスト
│   │   └── __init__.py             # テスト用パッケージ
│   └── __init__.py                 # Pythonパッケージとして認識させるためのファイル
├── cdk                              # AWS CDKによるIaC
│   ├── app_runner_stack.py         # App Runner関連のスタック定義
│   ├── codepipeline_stack.py       # CodePipeline/CodeBuild関連のスタック定義
│   ├── requirements.txt            # CDKで利用するPythonライブラリの依存関係
│   └── __init__.py                 # CDK用パッケージ
├── doc                              # ドキュメント類
│   └── how_to_use_bedrock_claude.md  # Claude(Bedrock)を使ったLLM実装ガイド、※編集禁止
├── env.example                       # 環境変数のサンプル
├── .gitignore                       # git管理除外ファイル
├── Dockerfile                       # Dockerビルド用
├── requirements.txt                 # アプリケーションのPython依存関係
└── README.md                        # プロジェクト全体の説明


```
#技術スタック
 - python3.11
 - fastAPI
 - docker
 - CI/CD : AWS CodePipeline/App Runner
 - AWS CDK(python)
 - コード管理:github
 - boto3: 1.36.0以上 (Bedrock APIサポートのため)
 - AWSのリージョン : ap-northeast-1 / Bedrockはus-west-2

## 遵守事項
 - ローカル実行時とDocker実行時の環境差分は.envファイルで管理
 - コードはブランチ管理
 - コードはブランチ管理
 - ブランチはmainとdevelopの2つ
 - ブランチはdevelopからmainへマージ
 - ブランチはdevelopからmainへマージ

# 環境構築の大枠の流れ
 - gitのURL、AWSの機密情報等を.envファイルに設定
 - ローカル環境構築
 - APIの動作確認
 - BedrockのAPI呼び出しの動作確認
 - Docker環境構築
 - APIの動作確認

## コーディング規約

### Python
- PEP 8に準拠
- 型ヒントを必須とする
- docstringはGoogle形式で記述
- 関数の行数は50行以内を目標
- PYTHONPATHはapp/srcに設定すること
- テストコードはapp/testsに配置すること
- モジュールのインポート規約：
  - app/src/endpoints/fortune.pyからインポートする場合は以下の形式を使用すること
    例: `from endpoints.fortune import fortune`

### FastAPI
- エンドポイントはOpenAPI仕様に準拠
- レスポンスモデルは必ずPydanticで定義
- エラーハンドリングは統一フォーマットで実装
- ミドルウェアの追加は影響範囲を考慮
- ローカル実行時とDocker実行時ではポートを変えること
- 起動前は必ずuvicornがすでに起動済みか確認し起動していたら停止すること


## セキュリティ
- センシティブなファイルは読み取り、編集不可
- 環境変数は.envファイルに保存
- シークレットは環境変数に保存
- ログにはシークレットを出力しない


## Sensitive Files

DO NOT read or modify:

-   .env files
-   *_/config/secrets._
-   *_/*.pem
-   Any file containing API keys, tokens, or credentials

## Security Practices

-   Never commit sensitive files
-   Use environment variables for secrets
-   Keep credentials out of logs and output

## Testing Standards

-   Unit tests required for business logic
-   Integration tests for API endpoints
-   E2E tests for critical user flows



上記を行うための環境設定手順を詳細にマークダウンで記述して

前提となる環境は必ずチェックをするような手順を組み込んでください
ローカル環境はMacを想定しています。
開発環境はローカル環境、Docker環境、AWS上の検証環境、本番環境を想定しています。