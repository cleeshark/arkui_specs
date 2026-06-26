
@Entry
@Component
export struct Case002AlignTopStart {
  build() {
    Stack() {
      Text('TopStart')
        .id('N_F02_S02_C002_TARGET')
        .width(100)
        .height(50)
        .backgroundColor('#2196F3')
    }
    .id('N_F02_S02_C002_PARENT')
    .width(300)
    .height(200)
    .align(Alignment.TopStart)
    .backgroundColor('#E0E0E0')
  }
}
