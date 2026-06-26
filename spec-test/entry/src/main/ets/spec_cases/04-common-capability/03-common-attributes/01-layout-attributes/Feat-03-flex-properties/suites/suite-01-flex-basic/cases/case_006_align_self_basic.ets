
@Entry
@Component
export struct Case006AlignSelfBasic {
  build() {
    Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Start }) {
      Text('A')
        .id('N_F03_C006_SIBLING')
        .width(80)
        .height(50)
        .fontSize(16)
        .backgroundColor('#E0E0E0')
      Text('B')
        .id('N_F03_C006_TARGET')
        .width(80)
        .height(50)
        .fontSize(16)
        .backgroundColor('#FF5722')
        .alignSelf(ItemAlign.End)
    }
    .id('N_F03_C006_PARENT')
    .width(300)
    .height(100)
  }
}
