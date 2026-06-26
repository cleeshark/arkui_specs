
@Entry
@Component
export struct Case001FlexGrowZeroDefault {
  build() {
    Flex({ direction: FlexDirection.Row }) {
      // A has flexGrow(0) explicitly - should not grow
      Text('A')
        .id('N_F03_S02_C001_TARGET_A')
        .width(50)
        .height(50)
        .backgroundColor('#4CAF50')
        .flexGrow(0)
      // B has flexGrow(1) - should take remaining space
      Text('B')
        .id('N_F03_S02_C001_TARGET_B')
        .width(50)
        .height(50)
        .backgroundColor('#2196F3')
        .flexGrow(1)
    }
    .id('N_F03_S02_C001_PARENT')
    .width(300)
    .height(100)
  }
}
