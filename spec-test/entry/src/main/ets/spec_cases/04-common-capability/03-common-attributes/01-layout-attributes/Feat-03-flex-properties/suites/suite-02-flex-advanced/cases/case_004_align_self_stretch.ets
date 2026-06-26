
@Entry
@Component
export struct Case004AlignSelfStretch {
  build() {
    Flex({ direction: FlexDirection.Row }) {
      Text('Stretch')
        .id('N_F03_S02_C004_TARGET')
        .width(100)
        .backgroundColor('#E91E63')
        .alignSelf(ItemAlign.Stretch)
    }
    .id('N_F03_S02_C004_PARENT')
    .width(300)
    .height(100)
  }
}
