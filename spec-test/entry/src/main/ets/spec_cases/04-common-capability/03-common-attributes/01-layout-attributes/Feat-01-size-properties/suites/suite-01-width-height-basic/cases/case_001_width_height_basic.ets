
@Entry
@Component
export struct Case001WidthHeightBasic {
  build() {
    RelativeContainer() {
      Text('C001')
        .id('N_F01_C001_TARGET')
        .width(100)
        .height(50)
        .fontSize(16)
        .alignRules({
          left: { anchor: '__container__', align: HorizontalAlign.Start },
          top: { anchor: '__container__', align: VerticalAlign.Top }
        })
    }
    .id('N_F01_C001_PARENT')
    .width(300)
    .height(300)
  }
}
