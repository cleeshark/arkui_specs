@Entry
@Component
export struct Case003WidthHeightZero {
  build() {
    RelativeContainer() {
      Text('C003')
        .id('N_F01_C003_TARGET')
        .width(0)
        .height(0)
        .fontSize(16)
        .alignRules({
          left: { anchor: '__container__', align: HorizontalAlign.Start },
          top: { anchor: '__container__', align: VerticalAlign.Top }
        })
    }
    .id('N_F01_C003_PARENT')
    .width(300)
    .height(300)
  }
}
