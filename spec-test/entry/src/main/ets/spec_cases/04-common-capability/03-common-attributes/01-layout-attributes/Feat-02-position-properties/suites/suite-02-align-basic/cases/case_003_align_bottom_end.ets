
@Entry
@Component
export struct Case003AlignBottomEnd {
  build() {
    Stack() {
      Text('BottomEnd')
        .id('N_F02_S02_C003_TARGET')
        .width(100)
        .height(50)
        .backgroundColor('#FF9800')
    }
    .id('N_F02_S02_C003_PARENT')
    .width(300)
    .height(200)
    .align(Alignment.BottomEnd)
    .backgroundColor('#E0E0E0')
  }
}
