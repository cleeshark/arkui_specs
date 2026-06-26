
@Entry
@Component
export struct Case004PercentWidth {
  build() {
    Column() {
      Text('50%')
        .id('N_F01_S02_C004_TARGET')
        .width('50%')
        .height(50)
        .backgroundColor('#9C27B0')
    }
    .id('N_F01_S02_C004_PARENT')
    .width(200)
    .height(100)
  }
}
