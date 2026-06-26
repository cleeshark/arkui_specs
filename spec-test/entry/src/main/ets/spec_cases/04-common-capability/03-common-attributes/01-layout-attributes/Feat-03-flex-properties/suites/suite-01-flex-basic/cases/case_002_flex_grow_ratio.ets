
@Entry
@Component
export struct Case002FlexGrowRatio {
  build() {
    Flex({ direction: FlexDirection.Row }) {
      Text('A')
        .id('N_F03_C002_TARGET_A')
        .width(0)
        .height(50)
        .fontSize(16)
        .backgroundColor('#4CAF50')
        .flexGrow(1)
      Text('B')
        .id('N_F03_C002_TARGET_B')
        .width(0)
        .height(50)
        .fontSize(16)
        .backgroundColor('#2196F3')
        .flexGrow(2)
    }
    .id('N_F03_C002_PARENT')
    .width(300)
    .height(100)
  }
}
