
@Entry
@Component
export struct Case002PositionOutOfLayout {
  build() {
    Column() {
      Text('A')
        .id('N_F02_C002_SIBLING')
        .width(60)
        .height(30)
        .fontSize(16)
        .backgroundColor('#E0E0E0')
      Text('B')
        .id('N_F02_C002_TARGET')
        .width(60)
        .height(30)
        .fontSize(16)
        .backgroundColor('#FFC107')
        .position({ x: 0, y: 0 })
      Text('C')
        .id('N_F02_C002_SIBLING2')
        .width(60)
        .height(30)
        .fontSize(16)
        .backgroundColor('#2196F3')
    }
    .id('N_F02_C002_PARENT')
    .width(300)
    .height(300)
    .alignItems(HorizontalAlign.Start)
  }
}
