
@Entry
@Component
export struct Case001AlignDefaultCenter {
  build() {
    Stack() {
      Text('Center')
        .id('N_F02_S02_C001_TARGET')
        .width(100)
        .height(50)
        .backgroundColor('#4CAF50')
    }
    .id('N_F02_S02_C001_PARENT')
    .width(300)
    .height(200)
    .backgroundColor('#E0E0E0')
  }
}
