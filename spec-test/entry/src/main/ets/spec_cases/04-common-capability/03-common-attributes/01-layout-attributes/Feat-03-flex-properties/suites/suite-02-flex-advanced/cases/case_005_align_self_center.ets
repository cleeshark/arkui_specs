
@Entry
@Component
export struct Case005AlignSelfCenter {
  build() {
    Flex({ direction: FlexDirection.Row, alignItems: ItemAlign.Start }) {
      Text('Center')
        .id('N_F03_S02_C005_TARGET')
        .width(100)
        .height(40)
        .backgroundColor('#00BCD4')
        .alignSelf(ItemAlign.Center)
    }
    .id('N_F03_S02_C005_PARENT')
    .width(300)
    .height(100)
  }
}
