@Entry
@Component
export struct Case007ButtonClickCallback {
  @State markerWidth: number = 100

  build() {
    Column() {
      Button('Click')
        .width(160)
        .height(48)
        .onClick(() => {
          this.markerWidth = 140
        })
      Text('callback')
        .id('N_BUTTON_US2_C007_TARGET')
        .width(this.markerWidth)
        .height(20)
    }
    .alignItems(HorizontalAlign.Start)
    .width(300)
    .height(200)
  }
}
