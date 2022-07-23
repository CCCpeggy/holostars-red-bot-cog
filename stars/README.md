# 直播通知

* 目前來源支援
    * holodex: 會自動偵測新影片
    * youtube: 需手動新增新影片

## 相關的指令

``` bash
-dstream 設置直播相關的
-dstream collab 設置聯動相關的
-dmember 設置成員相關的
-dchannel 設置頻道相關的
-dstarsset message 送出訊息的格式
```

## 加入要關注的頻道

``` bash
[p]member add [成員名稱]
[p]member set all [成員名稱] [通知頻道] [聊天頻道] [會員頻道] [紅色值] [綠色值] [藍色值] []
[p]channel add [成員名稱] [來源] [頻道 ID]
```

例子

``` bash
[p]member add izuru
[p]member set all izuru #通知 #聊天 #會員 70 0 255 🎸
[p]channel add izuru holodex UCZgOv3YDEs-ZnZWDYVwJdmA
```
