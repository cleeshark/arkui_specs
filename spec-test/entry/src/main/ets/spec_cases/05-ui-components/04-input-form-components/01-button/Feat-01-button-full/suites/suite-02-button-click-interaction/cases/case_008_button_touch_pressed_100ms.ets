@Entry
@Component
export struct Case008ButtonTouchPressed100ms {
  @State markerWidth: number = 100

  build() {
    Column() {
      Button('Press')
        .width(160)
        .height(48)
        .onTouch((event: TouchEvent) => {
          if (event.type === TouchType.Down) {
            this.markerWidth = 140
          }
        })
      Text('pressed')
        .id('N_BUTTON_US2_C008_TARGET')
        .width(this.markerWidth)
        .height(20)
    }
    .alignItems(HorizontalAlign.Start)
    .width(300)
    .height(200)
  }
}
