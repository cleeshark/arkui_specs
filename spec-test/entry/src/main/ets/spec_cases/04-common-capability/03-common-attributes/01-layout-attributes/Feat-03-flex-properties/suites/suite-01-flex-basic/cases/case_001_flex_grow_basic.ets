
@Entry
@Component
export struct Case001FlexGrowBasic {
  build() {
    Flex({ direction: FlexDirection.Row }) {
      Text('A')
        .id('N_F03_C001_SIBLING')
        .width(50)
        .height(50)
        .fontSize(16)
        .backgroundColor('#E0E0E0')
      Text('B')
        .id('N_F03_C001_TARGET')
        .height(50)
        .fontSize(16)
        .backgroundColor('#4CAF50')
        .flexGrow(1)
    }
    .id('N_F03_C001_PARENT')
    .width(300)
    .height(100)
  }
}
