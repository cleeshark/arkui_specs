
@Entry
@Component
export struct Case003FlexShrinkBasic {
  build() {
    Flex({ direction: FlexDirection.Row }) {
      Text('A')
        .id('N_F03_C003_TARGET_A')
        .width(150)
        .height(50)
        .fontSize(16)
        .backgroundColor('#4CAF50')
        .flexShrink(1)
      Text('B')
        .id('N_F03_C003_TARGET_B')
        .width(150)
        .height(50)
        .fontSize(16)
        .backgroundColor('#2196F3')
        .flexShrink(2)
    }
    .id('N_F03_C003_PARENT')
    .width(200)
    .height(100)
  }
}
