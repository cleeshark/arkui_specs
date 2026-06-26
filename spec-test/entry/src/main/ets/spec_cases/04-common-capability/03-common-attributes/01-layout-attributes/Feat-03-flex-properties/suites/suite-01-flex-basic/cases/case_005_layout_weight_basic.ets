
@Entry
@Component
export struct Case005LayoutWeightBasic {
  build() {
    Row() {
      Text('A')
        .id('N_F03_C005_TARGET_A')
        .height(50)
        .fontSize(16)
        .backgroundColor('#4CAF50')
        .layoutWeight(1)
      Text('B')
        .id('N_F03_C005_TARGET_B')
        .height(50)
        .fontSize(16)
        .backgroundColor('#2196F3')
        .layoutWeight(2)
    }
    .id('N_F03_C005_PARENT')
    .width(300)
    .height(100)
  }
}
