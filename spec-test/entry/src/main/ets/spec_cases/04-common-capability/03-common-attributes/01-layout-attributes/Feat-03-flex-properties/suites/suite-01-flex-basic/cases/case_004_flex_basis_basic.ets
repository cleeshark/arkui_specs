
@Entry
@Component
export struct Case004FlexBasisBasic {
  build() {
    Flex({ direction: FlexDirection.Row }) {
      Text('A')
        .id('N_F03_C004_TARGET')
        .height(50)
        .fontSize(16)
        .backgroundColor('#4CAF50')
        .flexBasis(100)
      Text('B')
        .id('N_F03_C004_SIBLING')
        .width(80)
        .height(50)
        .fontSize(16)
        .backgroundColor('#E0E0E0')
    }
    .id('N_F03_C004_PARENT')
    .width(300)
    .height(100)
  }
}
